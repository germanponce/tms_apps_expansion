# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import time
import math

from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from lxml import etree
from itertools import groupby
import logging
_logger = logging.getLogger(__name__)

class InvoicePaymentLineAdvance(models.TransientModel):
    """
    Batch payment record of supplier invoices
    """
    _name = "invoice.payment.line.advance"
    _rec_name = 'advance_id'

    advance_id = fields.Many2one('tms.advance', string="Anticipo",
                                 required=True)
    employee_id = fields.Many2one('hr.employee', string="Conductor",
                                 required=True)
    employee_name = fields.Char("Cliente", size=256,
                                 required=False)

    partner_id = fields.Many2one('res.partner', 'Empresa')

    balance_amt = fields.Float("Total", required=True)
    wizard_id = fields.Many2one('account.register.tms_advance_payments', string="Wizard")
    paying_amt = fields.Float("Monto a Pagar", required=True)
    
    advance_name =  fields.Char('Anticipo', size=256)
    payment_difference = fields.Float(string='Saldo Pendiente',
                                      readonly=True)
    handling = fields.Selection([('open', 'Mantener Abierta'),
                                 ('reconcile', 'Marcar Anticipo como Pagado')],
                                default='open',
                                string="Action",
                                copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Cuenta",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)
    @api.onchange('payment_difference')
    def onchange_payment_difference(self):
        if self.payment_difference > 0.0:
            self.handling = 'open'

    @api.onchange('paying_amt')
    def _onchange_amount(self):
        self.payment_difference = (self.balance_amt - self.paying_amt)

class account_register_tms_advance_payments(models.TransientModel):
    """
    Inheritance to make payments in batches
    """
    _inherit = "account.register.tms_advance_payments"

    @api.depends('advance_payments.paying_amt')
    def _compute_pay_total(self):
        for rec in self:
            rec.total_pay_amount = sum(line.paying_amt for line in
                                       rec.advance_payments)

    is_auto_fill = fields.Char(string="Saldo Automatico")
    advance_payments = fields.One2many('invoice.payment.line.advance', 'wizard_id',
                                       string='Payments')
    is_advance = fields.Boolean(string="Cliente?")

    cheque_amount = fields.Float("Monto a Validar", 
                                 required=True, default=0.00)
    total_pay_amount = fields.Float("Monto Total",
                                    compute='_compute_pay_total')

    error_in_batch = fields.Boolean('Error en Batch')

    pago_de_mas = fields.Boolean('Pago de Mas')

    amount_difference_plus = fields.Float('Monto Ajuste Mas', digits=(14,4))
    amount_difference_low = fields.Float('Monto Ajuste Menos', digits=(14,4))

    batch_writeoff_account_id = fields.Many2one('account.account', string="Cuenta Ajuste",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)

    batch_writeoff_text = fields.Char('Referencia Ajuste', size=256, default="Partida Ajuste de saldo")
    pago_de_menos = fields.Boolean('Pago de Menos con Conciliacion')

    payment_reference = fields.Char('Referencia del Pago', size=256)

    journal_batch_id = fields.Many2one('account.journal', 'Diario de Pago')


    @api.onchange('journal_batch_id')
    def onchange_journal_batch_id(self):
        context = dict(self._context or {})
        if 'batch' in context and context.get('batch'):
            if self.journal_batch_id:
                self.journal_id = self.journal_batch_id.id
    

    @api.multi
    def create_payments(self):
        res = super(account_register_tms_advance_payments, self).create_payments()
        for rec in self:
            context = self._context
            active_model = context.get('active_model')
            active_ids = context.get('active_ids')
            records_browse = self.env[active_model].browse(active_ids)
            for adv in records_browse:
                if adv.amount_payment_total > 0.0:
                    raise UserError("El Anticipo %s tiene un monto residual por ello debes utilizar el Asistente de Multiples Pagos. " % adv.name)
        return res

    @api.onchange('advance_payments',)
    def onchange_pago_de_mas(self):
        amount_difference_plus = 0.0
        pago_de_mas = False
        context = dict(self._context)
        pago_de_menos = False

        for paym in self.advance_payments:
            if paym.paying_amt and paym.payment_difference < 0.0:
                if paym.payment_difference - 0.0:
                    amount_difference_plus += paym.payment_difference
            if paym.handling == 'reconcile' and pago_de_menos == False:
                pago_de_menos = True

        if amount_difference_plus:
            self.pago_de_mas = True
            self.amount_difference_plus = amount_difference_plus
            if pago_de_menos:
                self.pago_de_mas = True


    @api.onchange('total_pay_amount','advance_payments',)
    def onchange_total_pay_amount(self):
        # print ("### onchange_total_pay_amount >>>>>> ",self.total_pay_amount)
        pago_de_menos_bef = self.pago_de_menos
        # print ("######### pago_de_menos_bef >>>>>>>> ",pago_de_menos_bef)
        if self.cheque_amount and self.total_pay_amount:
            self.cheque_amount = self.total_pay_amount
        if self.advance_payments:
            pago_de_menos = False
            for ln in self.advance_payments:
                if ln.handling == 'reconcile' and pago_de_menos == False:
                    pago_de_menos = True
                else:
                    if not pago_de_menos:
                        if ln.payment_difference < 0.0:
                            pago_de_menos = True
            # print ("####### pago_de_menos >>>>>>>> ",pago_de_menos)
            if pago_de_menos:
                self.pago_de_menos = pago_de_menos
                self.pago_de_mas = pago_de_menos
            else:
                if pago_de_menos_bef and not pago_de_menos:
                    self.pago_de_menos = pago_de_menos
                    self.pago_de_mas = pago_de_menos
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        domain_on_types = [('type', 'in', list(journal_types))]

        return {'domain': {'journal_batch_id': jrnl_filters['domain'] + domain_on_types}}


    @api.model
    def default_get(self, pfields):
        """
        Get list of bills to pay
        """
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        # Checks on context parameters
        if not active_model or not active_ids:
            raise UserError(
                _("Program error: wizard action executed without"
                  " active_model or active_ids in context."))

        # Checks on received invoice records
        records_browse = self.env[active_model].browse(active_ids)
        if any(instance_br.state != 'confirmed' for instance_br in records_browse):
            raise UserError(_("Solo puedes registrar pagos en Anticipos con Saldo"
                              " pendiente"))

        if any(adv.currency_id != records_browse[0].currency_id for adv in records_browse):
            raise UserError(_("Para pagar multiples facturas al mismo tiempo,"
                              " debes usar la misma moneda."))

        res = {}
        payment_method_default_id = False
        payment_obj = self.env['account.payment.method'].sudo()
        payment_search = payment_obj.search([])
        if payment_search:
            payment_method_default_id = payment_search[0].id
        
        amount_balance_result_global = 0.0
        if 'batch' in context and context.get('batch'):
            jrnl_filters = self._compute_journal_domain_and_types()
            journal_types = jrnl_filters['journal_types']
            domain_on_types = [('type', 'in', list(journal_types))]
            journal_batch_id = False
            if journal_types:
                journal_batch_id = self.env['account.journal'].search(domain_on_types, limit=1)
                if journal_batch_id:
                    journal_batch_id  = journal_batch_id.id

            if str(active_model) == 'tms.advance':
                res.update({'is_advance': True})
            lines = []
            for rec in records_browse:
                amount_balance_result = rec.amount_balance
                if amount_balance_result < 0.0:
                    amount_balance_result = 0.0
                if amount_balance_result == 0.0:
                    raise UserError("El Anticipo %s no tiene monto adeudado." % rec.name)
                amount_balance_result_global += amount_balance_result

                dict_line = {
                    'partner_id': rec.employee_id.address_home_id.id,
                    'employee_id': rec.employee_id.id,
                    'employee_name': rec.employee_id.name_get()[0][1],
                    'advance_name': rec.name if rec.name else rec.name_get()[0][1],
                    'advance_id': rec.id,
                    'balance_amt': amount_balance_result or 0.0,
                    'paying_amt': amount_balance_result,
                    'payment_method_id': payment_method_default_id,
                    'payment_difference': 0.0,
                }
                # print ("### DICT LINE >>>>> ",dict_line)
                lines.append((0, 0, dict_line))
            dict_val = {
                'advance_payments': lines,
                'is_advance': True,
                'journal_batch_id': journal_batch_id,
            }
            res.update(dict_val)


        if 'batch' in context and context.get('batch'):
            # total_amount = sum(
            #     rcs2.amount_balance for rcs2 in records_browse)
            total_amount = amount_balance_result_global

            dict_val_rec = {
                'amount': abs(total_amount),
                'currency_id': records_browse[0].currency_id.id,
                'payment_type': total_amount > 0 and 'inbound' or 'outbound',
                'partner_id': records_browse[0].employee_id.address_home_id.id,
                'partner_type': 'supplier',
            }
            res.update(dict_val_rec)

            res.update({
                'cheque_amount': total_amount,
                })
        else:
            res = super(account_register_tms_advance_payments, self).default_get(pfields)
        # print ("#### REC >>> ",res)
        payment_date = False
        if 'payment_date' not in res:
            payment_date = fields.Date.context_today(self)
        if 'payment_date' in res and not res['payment_date'] :
            payment_date = fields.Date.context_today(self)
        if payment_date:
            res.update({'payment_date':payment_date})
        
        res.update({
                'batch_writeoff_text':'Partida Ajuste de saldo',
                'show_communication_field': True,
                'communication' : ' '.join([ref for ref in records_browse.mapped('name')]),
            })

        return res


    def get_payment_batch_vals(self, group_data=None):
        # print ("######## group_data >>>>> ",group_data)
        active_ids = []
        if 'rec_val' in group_data:
            active_ids = list(group_data['rec_val'].keys())
            active_ids = [int(x) for x in active_ids]
        # print ("######### ACTIVE IDS >>>>>>>>> ",active_ids)
        advances = self.env['tms.advance'].browse(active_ids)
        amount = self._compute_payment_amount(advances=advances) or self.amount2 if self.multi else self.amount2
        payment_type = 'outbound'
        bank_account = self.partner_bank_account_id
        pmt_communication = self.show_communication_field and self.communication \
                            or ' '.join([adv.name for adv in advances]) 
        result_amount = group_data['total']
        payment_difference = 0.0
        if 'payment_difference' in group_data:
            payment_difference = group_data['payment_difference']
        # print ("#### PAYMENT DIFFERENCE >>>> ",payment_difference)

        amount_difference_plus = 0.0
        amount_difference_low = 0.0
        if 'amount_difference_plus' in group_data:
            amount_difference_plus = group_data['amount_difference_plus']
        if 'amount_difference_low' in group_data:
            amount_difference_low = group_data['amount_difference_low']
        # if self.pago_de_mas and payment_difference < 0.0:
        #     result_amount = result_amount + payment_difference
        new_rec = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': group_data['memo'],
            'tms_advance_ids': [(6, 0, advances.ids)],
            'payment_type': payment_type,
            'amount': result_amount,
            'currency_id': self.currency_id.id,
            'partner_id': advances[0].employee_id.address_home_id.id,
            'partner_type': 'supplier',
            'partner_bank_account_id': bank_account.id,
            'multi': False,
            'payment_reference': self.payment_reference if self.payment_reference else '',
            'pago_de_mas': True if amount_difference_plus < 0.0 else False,
            'pago_de_menos': True if amount_difference_low < 0.0 else False,
            # 'amount_difference_plus': payment_difference,
            'amount_difference_plus': amount_difference_plus,
            'amount_difference_low': amount_difference_low,
            'batch_writeoff_account_id': self.batch_writeoff_account_id.id if self.batch_writeoff_account_id else False,
            'batch_writeoff_text': self.batch_writeoff_text,
            'pago_de_menos': self.pago_de_menos,
        }

        return new_rec


    @api.multi
    def make_payments_supplier(self):
        """
        Dictionary for the payment to each supplier invoice
        """
        data = {}
        for paym in self.advance_payments:
            # if paym.paying_amt < paym.advance_id.total:
            #     raise UserError("No puedes pagar una cantidad menor.")
            if paym.paying_amt > 0:
                # print ("########## PAYING AMT > 0 ")
                partner_id = str(paym.partner_id.id)
                if partner_id in data:
                    old_total = data[partner_id]['total']
                    old_payment_difference = data[partner_id]['payment_difference']

                    old_amount_difference_plus = data[partner_id]['amount_difference_plus']
                    old_amount_difference_low = data[partner_id]['amount_difference_low']
                    # Build memo value
                    
                    p_memo = [
                        data[partner_id]['memo'], ' : ',
                        str(paym.advance_id.name)
                    ]
                    memo = ''.join(p_memo)
                    # Calculate amount in words
                    amount_total = old_total + paym.paying_amt
                    payment_difference = old_payment_difference + paym.payment_difference
                    amount_difference_plus = paym.payment_difference  if paym.payment_difference < 0.0 else 0.0
                    amount_difference_low = 0.0
                    if paym.handling == 'reconcile' and paym.payment_difference > 0.0:
                        amount_difference_low = paym.payment_difference  if paym.payment_difference > 0.0 else 0.0

                    amount_difference_plus = amount_difference_plus + old_amount_difference_plus
                    amount_difference_low = amount_difference_low + old_amount_difference_low

                    amount_word = \
                        self.currency_id.amount_to_text(amount_total)
                    dict_val_part_inv = {
                        'partner_id': partner_id,
                        'partner_type': 'supplier',
                        'total': amount_total,
                        'memo': memo,
                        'total_check_amount_in_words': amount_word,
                        'amount_difference_plus': amount_difference_plus,
                        'amount_difference_low': amount_difference_low,
                    }
                    if paym.payment_difference < 0.0:
                       dict_val_part_inv.update({
                        'payment_difference': payment_difference,
                        'writeoff_account_id': self.batch_writeoff_account_id.id if self.batch_writeoff_account_id else False,
                        'batch_writeoff_text': self.batch_writeoff_text,
                       }) 
                    data[partner_id].update(dict_val_part_inv)
                    dict_val_up = {
                                str(paym.advance_id.id): paym.paying_amt
                    }
                    


                    data[partner_id]['rec_val'].update(dict_val_up)
                else:
                    # Build memo value
                    memo = str(paym.advance_id.name)
                    # Calculate amount in words
                    amount_word = \
                        self.currency_id.amount_to_text(paym.paying_amt)
                    amount_difference_plus = paym.payment_difference  if paym.payment_difference < 0.0 else 0.0
                    amount_difference_low = 0.0
                    if paym.handling == 'reconcile' and paym.payment_difference > 0.0:
                        amount_difference_low = paym.payment_difference  if paym.payment_difference > 0.0 else 0.0

                    dict_val_up = {
                        partner_id: {
                            'partner_id': partner_id,
                            'partner_type': 'supplier',
                            'total': paym.paying_amt,
                            'memo': memo,
                            'payment_difference': paym.payment_difference,
                            'batch_writeoff_text': self.batch_writeoff_text,
                            'writeoff_account_id': paym.writeoff_account_id.id if paym.writeoff_account_id else False,
                            'amount_difference_plus': amount_difference_plus,
                            'amount_difference_low': amount_difference_low,
                            'rec_val': {
                                str(paym.advance_id.id): paym.paying_amt

                            }
                        }
                    }
                    data.update(dict_val_up)
        # print ("########## DATA >>>>>>>>>> ",data)
        return data

    @api.multi
    def make_payments(self):
        # print ("############## MAKE PAYMENTS ADVANCES >>>>>>>>> ")
        # Make group data either for Customers or Vendors
        context = dict(self._context or {})
        data = {}
        amount_difference_plus = 0.0

        if self.amount_difference_plus and not self.batch_writeoff_account_id:
            raise UserError("La cuenta de Ajuste es obligatoria cuando se intenta pagar una cantidad superior a la pendiente.")
        record_names = ""

        ######################################
        # print ("########  self.is_advance >>>>>> ",self.is_advance)
        context.update({'is_advance': True})
        # if self.total_pay_amount != self.cheque_amount:
        if "{0:.4f}".format(self.total_pay_amount) != "{0:.4f}".format(self.cheque_amount):
            raise ValidationError(_('Error en comprobacion! Monto total de Anticipos'
                                    ' El monto a Pagar y el monto ingresado para la verificación'
                                    ' deben ser iguales!'))

        for paym in self.advance_payments:
            if self.payment_reference:
                paym.advance_id.payment_reference = self.payment_reference

            if paym.advance_id:
                if record_names:
                    record_names =  record_names + "," + paym.advance_id.name if paym.advance_id.name else ""
                else:
                    record_names = paym.advance_id.name if paym.advance_id.name else ""
            amount_difference_plus += paym.balance_amt - paym.paying_amt
        data = self.make_payments_supplier()
        # print ("############## data >>>>>>>>>> ",data)
        # print ("############## record_names >>>>>>>>>> ",record_names)
        # print ("############## amount_difference_plus >>>>>>>>>> ",amount_difference_plus)
        # Update context
        dict_val = {
            'group_data': data
        }
        context.update(dict_val)
        # Making partner wise payment
        payment_ids = []
        # print ("### DATA >>> ",data)
        records_pago_menos = {}
        cr = self.env.cr

        cr.execute("""
            select advance_id, sum(payment_difference) from invoice_payment_line_advance
                where handling = 'reconcile' and wizard_id = %s group by advance_id;
            """, (self.id, ))
        cr_res = cr.fetchall()
        if cr_res and cr_res[0] and cr_res[0][0]:
            for dta in cr_res:
                records_pago_menos.update(
                    {dta[0]: dta[1]}
                    )
        # print ("######## records_pago_menos >>>> ",records_pago_menos)
        for p_index in list(data):
            val_ap = self.env['account.payment']
            group_data = data[p_index]

            # print ("######### group_data >>> ",group_data)
            payment_difference = 0.0
            if self.amount_difference_plus:
                payment_difference = self.amount_difference_plus
            writeoff_account_id = False
            if self.batch_writeoff_account_id:
                writeoff_account_id = self.batch_writeoff_account_id.id
            context.update ({
                    'payment_difference': payment_difference,
                    'writeoff_account_id': writeoff_account_id,
                    'record_names': record_names,
                    'batch_writeoff_text': self.batch_writeoff_text,
                })
            if records_pago_menos:
                context.update({
                    'records_pago_menos':records_pago_menos,
                    'pago_de_menos':True,
                    })
            payment_batch_vals = self.get_payment_batch_vals(group_data=group_data)
            # print ("########## payment_batch_vals >>> ",payment_batch_vals)
            # payment_batch_vals.update({
            #     'payment_reference': self.payment_reference if self.payment_reference else '',
            #     })
            # if writeoff_account_id and payment_difference:
            #     payment_batch_vals.update({
            #             'payment_difference': abs(self.amount_difference_plus),
            #             'payment_difference_handling': 'reconcile',
            #             'writeoff_account_id': writeoff_account_id,
            #             'writeoff_label': 'Ajuste Pago Extra para Facturas %s ' % record_names,
            #         })
                # print ("### PRUEBA >>> ")
            # print ("######### context >>>>>>>>> ",context)
            # print ("######### payment_batch_vals['tms_advance_ids'][0][2] >>>> ",payment_batch_vals['tms_advance_ids'][0][2])
            context2 = dict(context)
            context2.update({
                    'active_ids': payment_batch_vals['tms_advance_ids'][0][2],
                })
            payment = val_ap.with_context(context2).create(payment_batch_vals)
            
            ################ Multi Pagos Pendientes ################
            payment_register_obj = self.env['account.payment.tms.register']

            payment_register_vals = {
                                        'date': self.payment_date,
                                        'payment_id': payment.id,
                                        'amount_payment': 0.0,
                                        'advance_id': False,

                                    }
            if 'rec_val' in group_data:
                rec_val = group_data['rec_val']
                rec_val_ids = rec_val.keys()
                for rec_id in rec_val_ids:
                    amount_payment = rec_val[rec_id]
                    advance_id = int(rec_id)
                    payment_register_vals2 = payment_register_vals
                    payment_register_vals2.update({
                        'amount_payment': amount_payment,
                        'advance_id': advance_id,
                        })
                    # print ("### ADVANCE ID >>> ",rec_id)
                    # print ("### VALS >>> ",payment_register_vals2)
                    payment_register_id = payment_register_obj.create(payment_register_vals2)
                    #### Marcando los Anticipos con Accion Conciliar ####
                    if advance_id in records_pago_menos:
                        advance_br = self.env['tms.advance'].browse(advance_id)
                        advance_br.handling = 'reconcile'

            ################ Fin Multi Pagos Pendientes ################

            payment_ids.append(payment.id)
            # payment.post()
            payment.post_tms_advances_batch()


        view_id = self.env['ir.model.data'].get_object_reference(
            'account_payment_batch_process',
            'view_account_supplier_payment_tree_nocreate')[1]

        ##### Marcando como Pagas los Anticipos #####
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        records_browse = self.env[active_model].browse(active_ids)
        for adv2 in records_browse:
            if adv2.amount_balance <= 0.0 and adv2.paid == False:
                adv2.paid = True
                if adv2.handling == 'open':
                    adv2.handling = 'reconcile'
        # cr.execute("""
        #     update tms_advance set paid=True
        #         where amount_balance <= 0.0 and id in %s;
        #     """, (tuple(context_ids), ))
        # raise UserError("# AQUI >>> ")
        return {
            'name': _('Pagos'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'account.payment',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': "[('id','in',%s)]" % (payment_ids),
            'context': {'group_by': 'partner_id'}
        }

    @api.multi
    def _prepare_payment_vals(self, invoices):
        res = super(account_register_tms_advance_payments, self)._prepare_payment_vals(invoices)
        for rec in self:
            res.update({
                'payment_reference': rec.payment_reference if rec.payment_reference else '',
            })
        return res



class AccountPayment(models.Model):
    _inherit = "account.payment"

    pago_de_mas = fields.Boolean('Pago de Mas')

    amount_difference_plus = fields.Float('Monto Ajuste Mas', digits=(14,4))
    amount_difference_low = fields.Float('Monto Ajuste Menos', digits=(14,4))

    batch_writeoff_account_id = fields.Many2one('account.account', string="Cuenta Ajuste",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)

    batch_writeoff_text = fields.Char('Referencia Ajuste', size=256, default="Partida Ajuste de saldo")
    pago_de_menos = fields.Boolean('Pago de Menos con Conciliacion')


    @api.depends('state', 'tms_advance_ids')
    def _count_tms_advance(self):
        for rec in self:
            rec.advance_count = len(set(rec.tms_advance_ids.ids))
            

    @api.multi
    def post_tms_advances_batch(self):
        # print ("############# post_tms_advances_batch >>>>>>>>>> ")
        context = self._context
        # print ("###### CONTEXT >>>>>>>>>>>>>>>> ",context)
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("Solo puedes validar Pagos en Borrador."))

            # if any((adv.state != 'confirmed' or adv.paid) for adv in rec.tms_advance_ids):
            #     raise ValidationError(_("Uno de los Anticipos seleccionados ya se encuentra Pagado o aun no ha sido confirmado." ))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("Es necesario definir una secuencia para %s en la compañia %s.") % (sequence_code, self.env.user.company_id.name ))

            # Create the journal entry
            amount = rec.amount * (rec.payment_type in ('outbound', 'transfer') and 1 or -1)
            #move = rec._create_payment_entry(amount)
            move = rec._create_payment_entry_tms_advances_batch(amount)

            # In case of a transfer, the first journal entry created debited the source liquidity account and credited
            # the transfer account. Now we debit the transfer account and credit the destination liquidity account.
            if rec.payment_type == 'transfer':
                transfer_credit_aml = move.line_ids.filtered(lambda r: r.account_id == rec.company_id.transfer_account_id)
                transfer_debit_aml = rec._create_transfer_entry(amount)
                (transfer_credit_aml + transfer_debit_aml).reconcile()

            rec.write({'state': 'posted', 'move_name': move.name})
        #raise UserError('Pausa')
        return True
    
    
    def _create_payment_entry_tms_advances_batch(self, amount):
        """ Create a journal entry corresponding to a payment, if the payment references invoice(s) they are reconciled.
            Return the journal entry.
        """
        context = self._context
        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount, self.currency_id, self.company_id.currency_id)

        move = self.env['account.move'].create(self._get_move_vals())

        #Write line corresponding to invoice payment
        counterpart_aml_dict = self._get_shared_move_line_vals(debit, credit, amount_currency, move.id, False)
        counterpart_aml_dict.update(self._get_counterpart_move_line_vals_tms_advances_batch(self.tms_advance_ids))
        counterpart_aml_dict.update({'currency_id': currency_id})
        counterpart_aml = aml_obj.create(counterpart_aml_dict)

        #Reconcile with the invoices
        # if self.payment_difference_handling == 'reconcile' and self.payment_difference:
        #     writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
        #     debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(self.payment_difference, self.currency_id, self.company_id.currency_id)
        #     writeoff_line['name'] = self.writeoff_label
        #     writeoff_line['account_id'] = self.writeoff_account_id.id
        #     writeoff_line['debit'] = debit_wo
        #     writeoff_line['credit'] = credit_wo
        #     writeoff_line['amount_currency'] = amount_currency_wo
        #     writeoff_line['currency_id'] = currency_id
        #     writeoff_line = aml_obj.create(writeoff_line)
        #     if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
        #         counterpart_aml['debit'] += credit_wo - debit_wo
        #     if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
        #         counterpart_aml['credit'] += debit_wo - credit_wo
        #     counterpart_aml['amount_currency'] -= amount_currency_wo
        if self.amount_difference_plus < 0.0 and self.amount_difference_low > 0.0:
            difference = self.amount_difference_plus + self.amount_difference_low
            if difference < 0.0:
                ### Si se deja en Negativo Invierte la Poliza ###
                amount_difference_plus = abs(difference)
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount_difference_plus, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.batch_writeoff_text
                writeoff_line['account_id'] = self.batch_writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
            else:
                ### Si se deja en Negativo Invierte la Poliza ###
                amount_difference_low = abs(difference)
                amount_difference_low = amount_difference_low * -1
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount_difference_low, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.batch_writeoff_text
                writeoff_line['account_id'] = self.batch_writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo


        else:
            if self.amount_difference_plus < 0.0:
                ### Si se deja en Negativo Invierte la Poliza ###
                amount_difference_plus = abs(self.amount_difference_plus)
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount_difference_plus, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.batch_writeoff_text
                writeoff_line['account_id'] = self.batch_writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
            elif self.amount_difference_low > 0.0:
                ### Si se deja en Negativo Invierte la Poliza ###
                amount_difference_low = abs(self.amount_difference_low)
                amount_difference_low = amount_difference_low * -1
                writeoff_line = self._get_shared_move_line_vals(0, 0, 0, move.id, False)
                debit_wo, credit_wo, amount_currency_wo, currency_id = aml_obj.with_context(date=self.payment_date)._compute_amount_fields(amount_difference_low, self.currency_id, self.company_id.currency_id)
                writeoff_line['name'] = self.batch_writeoff_text
                writeoff_line['account_id'] = self.batch_writeoff_account_id.id
                writeoff_line['debit'] = debit_wo
                writeoff_line['credit'] = credit_wo
                writeoff_line['amount_currency'] = amount_currency_wo
                writeoff_line['currency_id'] = currency_id
                writeoff_line = aml_obj.create(writeoff_line)
                if counterpart_aml['debit'] or (writeoff_line['credit'] and not counterpart_aml['credit']):
                    counterpart_aml['debit'] += credit_wo - debit_wo
                if counterpart_aml['credit'] or (writeoff_line['debit'] and not counterpart_aml['debit']):
                    counterpart_aml['credit'] += debit_wo - credit_wo
                counterpart_aml['amount_currency'] -= amount_currency_wo
        #Write counterpart lines
        if not self.currency_id.is_zero(self.amount):
            if not self.currency_id != self.company_id.currency_id:
                amount_currency = 0
            liquidity_aml_dict = self._get_shared_move_line_vals(credit, debit, -amount_currency, move.id, False)
            liquidity_aml_dict.update(self._get_liquidity_move_line_vals(-amount))
            aml_obj.create(liquidity_aml_dict)

        #validate the payment
        if not self.journal_id.post_at_bank_rec:
            move.post()

        #reconcile the invoice receivable/payable line(s) with the payment
        if self.tms_advance_ids:
            self.tms_advance_ids.register_payment(counterpart_aml)
        ##### Ajustando la referencia #####
        if move and self.payment_reference:
            payment_rf = self.payment_reference
            self.env.cr.execute("""
                update account_move_line set payment_reference = %s where move_id= %s;
                """, (payment_rf, move.id,))

            self.env.cr.execute("""
                update account_move set payment_reference = %s where id= %s;
                """, (payment_rf, move.id,))

            self.env.cr.execute("""
                update account_move set partner_id=%s where id=%s;
                """, (self.partner_id.id, move.id,))

            self.env.cr.execute("""
                update account_move set amount = (select sum(debit) from account_move_line where move_id=account_move.id)  where id=%s;
                """, (move.id, ))

        return move
    
    
    def _get_counterpart_move_line_vals_tms_advances_batch(self, advances=False):
        if self.payment_type == 'transfer':
            name = self.name
        else:
            name = ''
            if self.partner_type == 'customer':
                if self.payment_type == 'inbound':
                    name += _("Customer Payment")
                elif self.payment_type == 'outbound':
                    name += _("Customer Credit Note")
            elif self.partner_type == 'supplier':
                if self.payment_type == 'inbound':
                    name += _("Vendor Credit Note")
                elif self.payment_type == 'outbound':
                    name += _("Vendor Payment")
            if advances:
                name += ': '
                for adv in advances:
                    if adv.move_id:
                        name += adv.name + ', '
                name = name[:len(name)-2]
        return {
            'name': name,
            'account_id': self.destination_account_id.id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False,
        }

    @api.multi
    def cancel(self):
        # print ("############ CANCELANDO EL PAGO >>>>>>>>>>>> ")
        for rec in self:
            if rec.tms_advance_ids:
                for adv in rec.tms_advance_ids:
                    # print ("############## adv.name >>> ",adv.name)
                    # print ("############## adv.paid >>> ",adv.paid)
                    if adv.paid:
                        adv.paid = False
                    if adv.handling == 'reconcile':
                        adv.handling = 'open'
        return super(AccountPayment,self).cancel()

################ Multi Pagos Pendientes ################

class TmsAdvance(models.Model):
    _name = 'tms.advance'
    _inherit ='tms.advance'


    @api.multi
    @api.depends('payment_register_ids')
    def _amount_all(self):
        for advance in self:
            balance = 0.0
            amount_payment_total = 0.0
            total = advance.total
            advance.update({
                        'amount_balance'            : 0.0,
                        'amount_balance2'           : 0.0,
                        'amount_payment_total'           : 0.0,
                              })
            for payment in advance.payment_register_ids:
                if payment.payment_id.state in ('reconciled','posted'):
                    amount_payment_total += payment.amount_payment
            if amount_payment_total:
                balance = total - amount_payment_total
                if balance <= 0.0:
                    balance = 0.0
            else:
                balance = total
            advance.update({
                        'amount_balance'            : advance.currency_id.round(balance),
                        'amount_balance2'           : advance.currency_id.round(balance),
                        'amount_payment_total'           : advance.currency_id.round(amount_payment_total),
                              })

    @api.one
    @api.depends('move_id', 'move_id.line_ids', 'move_id.line_ids.reconciled', 'payment_register_ids', 'payment_register_ids.payment_id', 'payment_register_ids.payment_id.state')
    def _paid(self):
        # print ("########## DEF _paid >>>>>>>>>>>>>>> ")
        # print ("########## SALDO PENDIENTE >>>>>>>>>>>>>>> ", self.amount_balance)
        val = False
        cr = self.env.cr
        if self.move_id:
            # print ("####### SI >>>>>> ")

            if self.payment_register_ids:
                balance = 0.0
                amount_payment_total = 0.0
                total = self.total

                for payment in self.payment_register_ids:
                    if payment.payment_id.state in ('reconciled','posted'):
                        amount_payment_total += payment.amount_payment
                if amount_payment_total:
                    balance = total - amount_payment_total
                    if balance <= 0.0:
                        balance = 0.0
                else:
                    balance = total
                # print ("######### balance >>>>>>> ",balance)
                # print ("######### amount_payment_total >>>>>>> ",amount_payment_total)
                # print ("######### total >>>>>>> ",total)
                if total <= amount_payment_total:
                    # print ("### MARCANDO COMO PAGADO >>> ")
                    val = True
                else:
                    # print ("## ELSE >>> ")
                    if self.handling == 'reconcile':
                        val = True
            else:
                if not val:
                    # print ("#### IF NOT VAL >>> ")
                    if not self.payment_register_ids:
                        for ml in self.move_id.line_ids:
                            if ml.account_id.internal_type in ('payable','receivable') \
                                and ml.credit > 0 and self.employee_id.address_home_id.id == ml.partner_id.id:
                                val = ml.reconciled
        self.paid = val

    amount_balance          = fields.Float(compute='_amount_all', digits=dp.get_precision('Sale Price'), 
                                           string='Saldo Pendiente')
    amount_balance2         = fields.Float(compute='_amount_all', digits=dp.get_precision('Sale Price'), 
                                           string='Saldp Pendiente2 ',)
    amount_payment_total    = fields.Float(compute='_amount_all', digits=dp.get_precision('Sale Price'), 
                                           string='Monto Pagado ',)

    handling = fields.Selection([('open', 'Mantener Abierta'),
                                 ('reconcile', 'Marcar Anticipo como Pagado')],
                                default='open',
                                string="Accion",
                                copy=False, readonly=True)

    payment_register_ids    = fields.One2many('account.payment.tms.register','advance_id', 'Pagos Efectuados')

    payment_rel_id = fields.Many2one('account.payment', 'Pago Relacionado', related="payment_register_ids.payment_id")

    payment_rel_reference = fields.Char('Ref. Pago', related="payment_register_ids.payment_reference", size=256)

class AccountPaymentTmsRegister(models.Model):
    _name = 'account.payment.tms.register'
    _description = 'Registro de Pagos'
    _order = 'date'
    _rec_name = 'payment_id' 

    date = fields.Date('Fecha Pago')
    payment_id = fields.Many2one('account.payment','Pago')
    amount_payment = fields.Float('Monto Pagado')
    payment_state = fields.Selection([('draft','Borrador'), ('posted','Publicado'),
                                      ('sent','Enviado'),('reconciled','Conciliado'),
                                      ('cancelled','Cancelado')],'Estado Pago', related="payment_id.state")
    payment_reference = fields.Char('Ref. Pago', related="payment_id.payment_reference", size=256)

    # ID Ref #
    advance_id = fields.Many2one('tms.advance', 'ID Ref Anticipo')
    expense_id = fields.Many2one('tms.expense', 'ID Ref Liquidacion')

################ FIN MULTIPAGOS ################