# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

INV_TO_PARTN = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}
# Since invoice amounts are unsigned, this is how we know if money comes in or
# goes out
INV_TO_PAYM_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit ='account.payment'

    payment_reference = fields.Char('Referencia del Pago', size=256)


class InvoiceCustomerPaymentLine(models.TransientModel):
    """
    batch payment record of customer invoices
    """
    _name = "invoice.customer.payment.line"
    _rec_name = 'invoice_id'

    invoice_id = fields.Many2one('account.invoice', string="Factura Cliente",
                                 required=True)
    partner_id = fields.Many2one('res.partner', string="Cliente",
                                 required=True)
    partner_name = fields.Char("Cliente", size=256,
                                 required=False)
    balance_amt = fields.Float("Saldo Factura", required=True)
    wizard_id = fields.Many2one('account.register.payments', string="Wizard")
    receiving_amt = fields.Float("Monto a Pagar", required=True)
    check_amount_in_words = fields.Char(string="Monto en Letra")
    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Tipo Pago')
    payment_difference = fields.Float(string='Saldo Pendiente',
                                      readonly=True)
    handling = fields.Selection([('open', 'Mantener Abierta'),
                                 ('reconcile', 'Marcar Factura como Pagada')],
                                default='open',
                                string="Action",
                                copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Cuenta",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)
    invoice_name =  fields.Char('Factura Cliente', size=256)

    @api.onchange('receiving_amt')
    def _onchange_amount(self):
        self.check_amount_in_words = \
            self.invoice_id.currency_id.amount_to_text(self.receiving_amt)
        self.payment_difference = (self.balance_amt - self.receiving_amt)


class InvoicePaymentLine(models.TransientModel):
    """
    Batch payment record of supplier invoices
    """
    _name = "invoice.payment.line"
    _rec_name = 'invoice_id'

    invoice_id = fields.Many2one('account.invoice', string="Factura Proveedor",
                                 required=True)
    partner_id = fields.Many2one('res.partner', string="Proveedor",
                                 required=True)
    partner_name = fields.Char("Cliente", size=256,
                                 required=False)
    balance_amt = fields.Float("Saldo Factura", required=True)
    wizard_id = fields.Many2one('account.register.payments', string="Wizard")
    paying_amt = fields.Float("Monto a Pagar", required=True)
    check_amount_in_words = fields.Char(string="Monto en Letra")
    invoice_name =  fields.Char('Factura Proveedor', size=256)
    payment_difference = fields.Float(string='Saldo Pendiente',
                                      readonly=True)
    handling = fields.Selection([('open', 'Mantener Abierta'),
                                 ('reconcile', 'Marcar Factura como Pagada')],
                                default='open',
                                string="Action",
                                copy=False)
    writeoff_account_id = fields.Many2one('account.account', string="Cuenta",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)

    @api.onchange('paying_amt')
    def _onchange_amount(self):
        self.check_amount_in_words = \
            self.invoice_id.currency_id.amount_to_text(self.paying_amt)
        self.payment_difference = (self.balance_amt - self.paying_amt)


    @api.onchange('payment_difference')
    def onchange_payment_difference(self):
        if self.payment_difference > 0.0:
            self.handling = 'open'


class AccountRegisterPayments(models.TransientModel):
    """
    Inheritance to make payments in batches
    """
    _inherit = "account.register.payments"

    @api.depends('invoice_customer_payments.receiving_amt')
    def _compute_customer_pay_total(self):
        for rec in self:
            rec.total_customer_pay_amount = sum(
                line.receiving_amt for line in rec.invoice_customer_payments)

    @api.depends('invoice_payments.paying_amt')
    def _compute_pay_total(self):
        for rec in self:
            rec.total_pay_amount = sum(line.paying_amt for line in
                                       rec.invoice_payments)

    is_auto_fill = fields.Char(string="Saldo Automatico")
    invoice_payments = fields.One2many('invoice.payment.line', 'wizard_id',
                                       string='Payments')
    is_customer = fields.Boolean(string="Cliente?")
    invoice_customer_payments = fields.One2many(
        'invoice.customer.payment.line',
        'wizard_id', string='Receipts')
    cheque_amount = fields.Float("Monto a Validar", 
                                 required=True, default=0.00)
    total_pay_amount = fields.Float("Monto Total",
                                    compute='_compute_pay_total')
    total_customer_pay_amount = fields.Float(
        "Monto Total", compute='_compute_customer_pay_total')

    error_in_batch = fields.Boolean('Error en Batch')

    pago_de_mas = fields.Boolean('Pago de Mas')

    amount_difference_plus = fields.Float('Monto Ajuste', digits=(14,4))

    batch_writeoff_account_id = fields.Many2one('account.account', string="Cuenta Ajuste",
                                          domain=[('deprecated', '=', False)],
                                          copy=False)

    batch_writeoff_text = fields.Char('Referencia Ajuste', size=256, default="Partida Ajuste de saldo")
    pago_de_menos = fields.Boolean('Pago de Menos con Conciliacion')

    payment_reference = fields.Char('Referencia del Pago', size=256)

    has_invoices = fields.Boolean('Tiene Facturas', default=True)

    @api.onchange('invoice_payments', 'invoice_customer_payments')
    def onchange_pago_de_mas(self):
        amount_difference_plus = 0.0
        pago_de_mas = False
        context = dict(self._context)
        pago_de_menos = False
        if self.is_customer:
            context.update({'is_customer': True})
            for paym in self.invoice_customer_payments:
                if paym.receiving_amt and paym.payment_difference < 0.0:
                    if paym.payment_difference - 0.0:
                        amount_difference_plus += paym.payment_difference
        else:
            for paym in self.invoice_payments:
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


    @api.onchange('total_pay_amount','invoice_payments','invoice_customer_payments')
    def onchange_total_pay_amount(self):
        # print ("### onchange_total_pay_amount >>>>>> ",self.total_pay_amount)
        if self.cheque_amount and self.total_pay_amount:
            self.cheque_amount = self.total_pay_amount
        if self.invoice_payments:
            pago_de_menos = False
            for ln in self.invoice_payments:
                if ln.handling == 'reconcile' and pago_de_menos == False:
                    pago_de_menos = True
            if pago_de_menos:
                self.pago_de_menos = pago_de_menos
                self.pago_de_mas = pago_de_menos
        if self.invoice_customer_payments:
            if self.cheque_amount and self.total_customer_pay_amount:
                self.cheque_amount = self.total_customer_pay_amount

    
    

    @api.onchange('journal_id')
    def onchange_recompute_multi_amounts(self):
        if self.invoice_customer_payments and self.journal_id:
            user = self.env.user.sudo()
            currency_invoice = self.invoice_customer_payments[0].invoice_id.currency_id
            currency_journal = self.journal_id.currency_id
            if not currency_journal:
                currency_journal = user.company_id.currency_id
            if currency_invoice != currency_journal:
                self.error_in_batch = True
                # raise UserError("Error!\nEl Diario debe contener la misma moneda que las Facturas.")
                self.journal_id = False
                # for payment in self.invoice_customer_payments:
                #     conversion_amount = 0.0
                #     balance_amt = payment.balance_amt
                #     payment_currency_id = currency_journal
                #     payment_date = self.payment_date 
                #     if not payment_date:
                #         payment_date = fields.Date.context_today(self)

                #     payment_amount = payment_currency_id.with_context(date=payment_date).compute(balance_amt, currency_invoice)
                #     print "#### payment_amount >>>>>>>>>>> ",payment_amount
                #     payment.balance_amt = conversion_amount


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
        if active_model != 'account.invoice':
            raise UserError(
                _("Program error: the expected model for this"
                  " action is 'account.invoice'. The provided one"
                  " is '%d'.") % active_model)

        # Checks on received invoice records
        invoices = self.env[active_model].browse(active_ids)
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("Solo puedes registrar pagos en Facturas con Saldo"
                              " pendiente"))
        if any(INV_TO_PARTN[inv.type] != INV_TO_PARTN[invoices[0].type]
               for inv in invoices):
            raise UserError(_("No puedes mezclar Facturas de Clietne y Proveedor"
                              " en un solo Pago."))
        if any(inv.currency_id != invoices[0].currency_id for inv in invoices):
            raise UserError(_("Para pagar multiples facturas al mismo tiempo,"
                              " debes usar la misma moneda."))

        rec = {}
        payment_method_default_id = False
        payment_obj = self.env['account.payment.method'].sudo()
        payment_search = payment_obj.search([])
        if payment_search:
            payment_method_default_id = payment_search[0].id

        if 'batch' in context and context.get('batch'):
            lines = []
            if INV_TO_PARTN[invoices[0].type] == 'customer':
                for inv in invoices:
                    dict_line = {
                        'partner_id': inv.partner_id.id,
                        'partner_name': inv.partner_id.name_get()[0][1],
                        'invoice_id': inv.id,
                        'invoice_name': inv.number if inv.number else inv.name_get()[0][1],
                        'balance_amt': inv.residual or 0.0,
                        'receiving_amt': 0.0,
                        'payment_difference': inv.residual or 0.0,
                        'handling': 'open',
                        'payment_method_id': payment_method_default_id,
                    }
                    lines.append((0, 0, dict_line))
                dict_val = {
                    'invoice_customer_payments': lines,
                    'is_customer': True
                }
                rec.update(dict_val)
            else:
                for inv in invoices:
                    dict_line = {
                        'partner_id': inv.partner_id.id,
                        'partner_name': inv.partner_id.name_get()[0][1],
                        'invoice_name': inv.number if inv.number else inv.name_get()[0][1],
                        'invoice_id': inv.id,
                        'balance_amt': inv.residual or 0.0,
                        'paying_amt': 0.0,
                        'payment_method_id': payment_method_default_id,
                    }
                    lines.append((0, 0, dict_line))
                dict_val = {
                    'invoice_payments': lines,
                    'is_customer': False
                }
                rec.update(dict_val)

        else:
            # Checks on received invoice records
            if any(INV_TO_PARTN[inv.type] != INV_TO_PARTN[invoices[0].type]
                   for inv in invoices):
                raise UserError(_("No puedes mezclar Facturas de Clietne y Proveedor"
                                  " en un solo Pago."))

        if 'batch' in context and context.get('batch'):
            total_amount = sum(
                inv.residual * INV_TO_PAYM_SIGN[inv.type] for inv in invoices)

            dict_val_rec = {
                'amount': abs(total_amount),
                'currency_id': invoices[0].currency_id.id,
                'payment_type': total_amount > 0 and 'inbound' or 'outbound',
                'partner_id': invoices[0].commercial_partner_id.id,
                'partner_type': INV_TO_PARTN[invoices[0].type],
                'journal_id': False,
            }
            rec.update(dict_val_rec)
        else:
            rec = super(AccountRegisterPayments, self).default_get(pfields)
        # print ("#### REC >>> ",rec)
        payment_date = False
        if 'payment_date' not in rec:
            payment_date = fields.Date.context_today(self)
        if 'payment_date' in rec and not rec['payment_date'] :
            payment_date = fields.Date.context_today(self)
        if payment_date:
            rec.update({'payment_date':payment_date})

        rec.update({'batch_writeoff_text':'Partida Ajuste de saldo'})

        return rec

    def get_payment_batch_vals(self, group_data=None):
        """
        Get values to save in the batch payment
        """
        if not group_data:
            return {}

        val_payment_m = \
            group_data['payment_method_id'] \
            if 'payment_method_id' in group_data \
            else self.payment_method_id.id
        # if not val_payment_m:
        #     payment_obj = self.env['account.payment.method'].sudo()
        #     payment_search = payment_obj.search([])
        #     if payment_search:
        #         val_payment_m = payment_search[0].id
        res = {
            'journal_id': self.journal_id.id,
            'payment_method_id': val_payment_m,
            'payment_date': self.payment_date,
            'communication': group_data['memo'],
            'invoice_ids': [(4, int(inv), None)
                            for inv in list(group_data['inv_val'])],
            'payment_type': self.payment_type,
            'amount': group_data['total'],
            'currency_id': self.currency_id.id,
            'partner_id': int(group_data['partner_id']),
            'partner_type': group_data['partner_type'],
            'payment_reference': self.payment_reference if self.payment_reference else '',
        }
        # if self.payment_reference:
        #     res.update({
        #                  'communication': 'REF: '+self.payment_reference+' - '+group_data['memo'],
        #         })
        p_model = self.env.ref(
            'account_check_printing.account_payment_method_check')
        if self.payment_method_id == p_model:
            p_data_total = group_data['total_check_amount_in_words']
            dict_val_rec = {
                'check_amount_in_words': p_data_total or '',
            }
            res.update(dict_val_rec)
        if 'partner_type' in group_data and group_data['partner_type'] == 'customer':
            for rec in self:
                res.update({
                    'user_id'       : rec.user_id.id,
                    'num_operacion' : rec.num_operacion,
                    'pay_method_id' : rec.pay_method_id and rec.pay_method_id.id or False,
                    'generar_cfdi'  : rec.generar_cfdi,
                    'no_data_bank_in_xml'  : rec.no_data_bank_in_xml,
                    'payment_datetime_reception' : rec.payment_datetime_reception,
                    'partner_acc_id': rec.partner_acc_id.id,
                    'partner_parent_id': rec.partner_parent_id.id,
                })
        return res

    @api.multi
    def make_payments_customer(self):
        """
        Dictionary for the payment to each customer invoice
        """
        data = {}
        for paym in self.invoice_customer_payments:
            if paym.receiving_amt > 0:
                paym.payment_difference = \
                    (paym.balance_amt - paym.receiving_amt)
                partner_id = str(paym.invoice_id.partner_id.id)
                if partner_id in data:
                    old_total = data[partner_id]['total']
                    # Build memo value
                    if self.communication:
                        memo = ''.join([data[partner_id]['memo'], ' : ',
                                        self.communication, '-',
                                        str(paym.invoice_id.number)])
                    else:
                        p_memo = [data[partner_id]['memo'], ' : ',
                                  str(paym.invoice_id.number)]
                        memo = ''.join(p_memo)
                    # Calculate amount in words
                    amount_total = (old_total + paym.receiving_amt)
                    amount_word = \
                        self.currency_id.amount_to_text(amount_total)
                    p_method_pay = \
                        paym.payment_method_id.id \
                        if paym.payment_method_id else False

                    # if not p_method_pay:
                    #     payment_obj = self.env['account.payment.method'].sudo()
                    #     payment_search = payment_obj.search([])
                    #     if payment_search:
                    #         p_method_pay = payment_search[0].id

                    dict_data_part = {
                        'partner_id': partner_id,
                        'partner_type': INV_TO_PARTN[paym.invoice_id.type],
                        'total': amount_total,
                        'memo': memo,
                        'payment_method_id': p_method_pay,
                        'total_check_amount_in_words': amount_word
                    }
                    data[partner_id].update(dict_data_part)
                    dict_data_part_inv = {
                        str(paym.invoice_id.id): {
                            'receiving_amt': paym.receiving_amt,
                            'handling': paym.handling,
                            'payment_difference': paym.payment_difference,
                            'writeoff_account_id': paym.writeoff_account_id and
                            paym.writeoff_account_id.id or False
                        }
                    }
                    data[partner_id]['inv_val'].update(dict_data_part_inv)
                else:
                    # Build memo value
                    if self.communication:
                        memo = ''.join([self.communication, '-',
                                        str(paym.invoice_id.number)])
                    else:
                        memo = str(paym.invoice_id.number)
                    # Calculate amount in words
                    dict_payment_method_id = \
                        paym.payment_method_id.id \
                        if paym.payment_method_id else False
                    amount_word = self.currency_id.amount_to_text(
                        paym.receiving_amt)
                    dict_writeoff_account_id = \
                        paym.writeoff_account_id.id \
                        if paym.writeoff_account_id else False

                    # if not dict_payment_method_id:
                    #     payment_obj = self.env['account.payment.method'].sudo()
                    #     payment_search = payment_obj.search([])
                    #     if payment_search:
                    #         dict_payment_method_id = payment_search[0].id

                    dict_data_upd = {
                        partner_id: {
                            'partner_id': partner_id,
                            'partner_type': INV_TO_PARTN[
                                paym.invoice_id.type],
                            'total': paym.receiving_amt,
                            'payment_method_id': dict_payment_method_id,
                            'total_check_amount_in_words': amount_word,
                            'memo': memo,
                            'inv_val': {
                                str(paym.invoice_id.id): {
                                    'receiving_amt': paym.receiving_amt,
                                    'handling': paym.handling,
                                    'payment_difference':
                                    paym.payment_difference,
                                    'writeoff_account_id':
                                    dict_writeoff_account_id
                                }
                            }
                        }
                    }
                    data.update(dict_data_upd)
        return data

    @api.multi
    def make_payments_supplier(self):
        """
        Dictionary for the payment to each supplier invoice
        """
        data = {}
        for paym in self.invoice_payments:
            if paym.paying_amt > 0:
                partner_id = str(paym.invoice_id.partner_id.id)
                if partner_id in data:
                    old_total = data[partner_id]['total']
                    # Build memo value
                    if self.communication:
                        p_memo = [
                            data[partner_id]['memo'], ' : ',
                            self.communication, '-',
                            str(paym.invoice_id.number)
                        ]
                        memo = ''.join(p_memo)
                    else:
                        p_memo = [
                            data[partner_id]['memo'], ' : ',
                            str(paym.invoice_id.number)
                        ]
                        memo = ''.join(p_memo)
                    # Calculate amount in words
                    amount_total = old_total + paym.paying_amt
                    amount_word = \
                        self.currency_id.amount_to_text(amount_total)
                    dict_val_part_inv = {
                        'partner_id': partner_id,
                        'partner_type': INV_TO_PARTN[
                            paym.invoice_id.type],
                        'total': amount_total,
                        'memo': memo,
                        'total_check_amount_in_words': amount_word
                    }
                    if paym.payment_difference < 0.0:
                       dict_val_part_inv.update({
                        'payment_difference': paym.payment_difference,
                        'writeoff_account_id': self.batch_writeoff_account_id.id if self.batch_writeoff_account_id else False,
                        'batch_writeoff_text': self.batch_writeoff_text,
                       }) 
                    data[partner_id].update(dict_val_part_inv)
                    dict_val_up = {
                        str(paym.invoice_id.id): paym.paying_amt
                    }
                    


                    data[partner_id]['inv_val'].update(dict_val_up)
                else:
                    # Build memo value
                    if self.communication:
                        p_memo = [
                            self.communication, '-',
                            str(paym.invoice_id.number)
                        ]
                        memo = ''.join(p_memo)
                    else:
                        memo = str(paym.invoice_id.number)
                    # Calculate amount in words
                    amount_word = \
                        self.currency_id.amount_to_text(paym.paying_amt)
                    dict_val_up = {
                        partner_id: {
                            'partner_id': partner_id,
                            'partner_type': INV_TO_PARTN[
                                paym.invoice_id.type],
                            'total': paym.paying_amt,
                            'total_check_amount_in_words': amount_word,
                            'memo': memo,
                            'payment_difference': paym.payment_difference,
                            'writeoff_account_id': paym.writeoff_account_id.id if paym.writeoff_account_id else False,
                            'inv_val': {
                                str(paym.invoice_id.id): paym.paying_amt

                            }
                        }
                    }
                    data.update(dict_val_up)
        return data

    @api.multi
    def make_payments(self):
        """
        Action make payments
        """
        # Make group data either for Customers or Vendors
        context = dict(self._context or {})
        data = {}
        amount_difference_plus = 0.0

        if self.amount_difference_plus and not self.batch_writeoff_account_id:
            raise UserError("La cuenta de Ajuste es obligatoria cuando se intenta pagar una cantidad superior a la pendiente.")
        invoice_names = ""
        ### **** Solo para Belchez **** ####
        if self.group_invoices:
            raise UserError("No puedes agrupar las Facturas en este proceso.")
        ######################################
        if self.is_customer:
            context.update({'is_customer': True})
            # if self.total_customer_pay_amount != self.cheque_amount:
            if "{0:.4f}".format(self.total_customer_pay_amount) != "{0:.4f}".format(self.cheque_amount):
                raise ValidationError(_('Error en comprobacion! Monto total de Facturas'
                                        ' El monto a Pagar y el monto ingresado para la verificación'
                                        ' deben ser iguales!'))
            if self.error_in_batch:
                raise UserError("Error!\nEl Diario debe contener la misma moneda que las Facturas.")
            for paym in self.invoice_customer_payments:
                if paym.invoice_id:
                    if invoice_names:
                        invoice_names =  invoice_names + "," + paym.invoice_id.number if paym.invoice_id.number else ""
                    else:
                        invoice_names = paym.invoice_id.number if paym.invoice_id.number else ""
                if self.is_customer:
                    if (paym.balance_amt - paym.receiving_amt) < 0.00:
                        amount_difference_plus += paym.balance_amt - paym.receiving_amt
                        # raise ValidationError(
                        #     _('Error en comprobacion!  Monto'
                        #       ' no puede ser mas grande'))

                if not paym.payment_method_id:
                    raise ValidationError(
                        _('Error en comprobacion! Tipo de Pago'
                          ' debe ser indicado.'))

            data = self.make_payments_customer()

        else:
            if self.generar_cfdi:
                raise UserError("No se puede generar un CFDI en Pago a Proveedores.")
            context.update({'is_customer': False})
            # if self.total_pay_amount != self.cheque_amount:
            if "{0:.4f}".format(self.total_pay_amount) != "{0:.4f}".format(self.cheque_amount):
                raise ValidationError(_('Error en comprobacion! Monto total de Facturas'
                                        ' El monto a Pagar y el monto ingresado para la verificación'
                                        ' deben ser iguales!'))

            for paym in self.invoice_payments:
                if paym.invoice_id:
                    if invoice_names:
                        invoice_names =  invoice_names + "," + paym.invoice_id.number if paym.invoice_id.number else ""
                    else:
                        invoice_names = paym.invoice_id.number if paym.invoice_id.number else ""
                amount_difference_plus += paym.balance_amt - paym.paying_amt
                # if paym.balance_amt < paym.paying_amt:
                #     paym.paying_amt = paym.balance_amt
                ### Solo permitido para Proveedores ####
                # if self.is_customer:
                #     if (paym.balance_amt - paym.paying_amt) < 0.00:
                #         raise ValidationError(
                #             _('Error en comprobacion!  Monto'
                #               ' no puede ser mas grande'))

            data = self.make_payments_supplier()
        # Update context
        dict_val = {
            'group_data': data
        }
        context.update(dict_val)
        # Making partner wise payment
        payment_ids = []
        # print ("### DATA >>> ",data)
        facturas_pago_menos = {}
        cr = self.env.cr
        if self.invoice_customer_payments:
            cr.execute("""
                select invoice_id, payment_difference from invoice_customer_payment_line
                    where handling = 'reconcile' and wizard_id = %s;
                """, (self.id, ))
            cr_res = cr.fetchall()
            if cr_res and cr_res[0] and cr_res[0][0]:
                for dta in cr_res:
                    facturas_pago_menos.update(
                        {dta[0]: dta[1]}
                        )
        else:
            
            cr.execute("""
                select invoice_id, payment_difference from invoice_payment_line
                    where handling = 'reconcile' and wizard_id = %s;
                """, (self.id, ))
            cr_res = cr.fetchall()
            if cr_res and cr_res[0] and cr_res[0][0]:
                for dta in cr_res:
                    facturas_pago_menos.update(
                        {dta[0]: dta[1]}
                        )
        # print ("######## facturas_pago_menos >>>> ",facturas_pago_menos)
        for p_index in list(data):
            val_ap = self.env['account.payment']
            group_data = data[p_index]
            payment_difference = 0.0
            if self.amount_difference_plus:
                payment_difference = self.amount_difference_plus
            writeoff_account_id = False
            if self.batch_writeoff_account_id:
                writeoff_account_id = self.batch_writeoff_account_id.id
            context.update ({
                    'payment_difference': payment_difference,
                    'writeoff_account_id': writeoff_account_id,
                    'invoice_names': invoice_names,
                    'batch_writeoff_text': self.batch_writeoff_text,
                })
            if facturas_pago_menos:
                context.update({
                    'facturas_pago_menos':facturas_pago_menos,
                    'pago_de_menos':True,
                    })
            payment_batch_vals = self.get_payment_batch_vals(group_data=group_data)
            # payment_batch_vals.update({
            #     'payment_reference': self.payment_reference if self.payment_reference else '',
            #     })
            # if writeoff_account_id and payment_difference:
            #     payment_batch_vals.update({
            #             'payment_difference': abs(self.amount_difference_plus),
            #             'payment_difference_handling': 'reconcile',
            #             'writeoff_account_id': writeoff_account_id,
            #             'writeoff_label': 'Ajuste Pago Extra para Facturas %s ' % invoice_names,
            #         })
            #     print ("### PRUEBA >>> ")
            context2 = dict(context)
            context2.update({
                    'active_ids': payment_batch_vals['invoice_ids'][0][2],
                })
            payment = val_ap.with_context(context2).create(payment_batch_vals)
            payment_ids.append(payment.id)
            payment.post()
            _logger.info("\n:::::: Tratando de Agrupar los apuntes contables del Pago.")
            payment.group_moves_data_in_payment()

        view_id = self.env['ir.model.data'].get_object_reference(
            'account_payment_batch_process',
            'view_account_supplier_payment_tree_nocreate')[1]
        #raise UserError("# AQUI >>> ")
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
        res = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices)
        for rec in self:
            res.update({
                'payment_reference': rec.payment_reference if rec.payment_reference else '',
            })
        return res


    # @api.multi
    # def auto_fill_payments(self):
    #     """
    #     Action auto fill payments
    #     """
    #     ctx = self._context.copy()
    #     for wiz in self:
    #         if wiz.is_customer:
    #             if wiz.invoice_customer_payments:
    #                 for payline in wiz.invoice_customer_payments:
    #                     payline.write({'receiving_amt': payline.balance_amt,
    #                                    'payment_difference': 0.0})
    #             ctx.update({'reference': wiz.communication or '',
    #                         'journal_id': wiz.journal_id.id})
    #         else:
    #             if wiz.invoice_payments:
    #                 for payline in wiz.invoice_payments:
    #                     payline.write({'paying_amt': payline.balance_amt})
    #             ctx.update({'reference': wiz.communication or '',
    #                         'journal_id': wiz.journal_id.id})

    #     return {
    #         'name': _("Batch Payments"),
    #         'view_mode': 'form',
    #         'view_id': False,
    #         'view_type': 'form',
    #         'res_id': self.id,
    #         'res_model': 'account.register.payments',
    #         'type': 'ir.actions.act_window',
    #         'nodestroy': True,
    #         'target': 'new',
    #         'context': ctx
    #     }

    @api.multi
    def auto_fill_payments(self):
        ctx = self._context.copy()
        wiz_total = 0.0
        cr = self.env.cr
        for wiz in self:
            if wiz.is_customer:
                if wiz.invoice_customer_payments:
                    cr.execute("""
                        update invoice_customer_payment_line
                            set receiving_amt = balance_amt,
                                payment_difference = 0.0
                                where wizard_id = %s;
                        """, (wiz.id, ))
                    cr.execute("""
                        update invoice_customer_payment_line
                            set invoice_name = account_invoice.number
                                from account_invoice where account_invoice.id = invoice_customer_payment_line.invoice_id
                                and invoice_customer_payment_line.wizard_id = %s;
                        """, (wiz.id, ))
                    cr.execute("""
                        update invoice_customer_payment_line
                            set partner_name = res_partner.name
                                from res_partner where res_partner.id = invoice_customer_payment_line.partner_id
                                and invoice_customer_payment_line.wizard_id = %s;
                        """, (wiz.id, ))

                    # cr.execute("""
                    #     update invoice_customer_payment_line
                    #         set handling = 'reconcile'
                    #         where payment_difference <= 0.0
                    #         and wizard_id = %s;
                    #     """, (wiz.id, ))
                    cr.execute("""
                        select sum(balance_amt) from invoice_customer_payment_line
                                where wizard_id = %s;
                        """, (wiz.id, ))
                    cr_res = cr.fetchall()
                    try:
                        wiz_total = float(cr_res[0][0])
                    except:
                        wiz_total = 0.0
                    # for payline in wiz.invoice_customer_payments:
                    #     wiz_total += payline.balance_amt
                    #     payline.write({'receiving_amt': payline.balance_amt,
                    #                    'payment_difference': 0.0})
                ctx.update({'reference': wiz.communication or '',
                            'journal_id': wiz.journal_id.id})
            else:
                if wiz.invoice_payments:
                    cr.execute("""
                        update invoice_payment_line
                            set paying_amt = balance_amt,
                                payment_difference = 0.0
                                where wizard_id = %s;
                        """, (wiz.id, ))
                    cr.execute("""
                        update invoice_payment_line
                            set invoice_name = account_invoice.number
                                from account_invoice where account_invoice.id = invoice_payment_line.invoice_id
                                and invoice_payment_line.wizard_id = %s;
                        """, (wiz.id, ))
                    cr.execute("""
                        update invoice_payment_line
                            set partner_name = res_partner.name
                                from res_partner where res_partner.id = invoice_payment_line.partner_id
                                and invoice_payment_line.wizard_id = %s;
                        """, (wiz.id, ))


                    cr.execute("""
                        select sum(balance_amt) from invoice_payment_line
                                where wizard_id = %s;
                        """, (wiz.id, ))
                    cr_res = cr.fetchall()
                    try:
                        wiz_total = float(cr_res[0][0])
                    except:
                        wiz_total = 0.0

                    # for payline in wiz.invoice_payments:
                    #     wiz_total += payline.balance_amt
                    #     payline.write({'paying_amt': payline.balance_amt})
                ctx.update({'reference': wiz.communication or '',
                            'journal_id': wiz.journal_id.id})
            wiz.cheque_amount = wiz_total
        return {
            'name': _("Asistente Multiples Pagos"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_id': self.id,
            'res_model': 'account.register.payments',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'new',
            'context': ctx
        }



