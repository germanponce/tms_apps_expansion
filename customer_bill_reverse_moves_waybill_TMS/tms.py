# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to German Ponce Dominguez :D
#    info skype: german_442 email: (german.ponce@argil.mx)
############################################################################
#    Coded by: german_442 email: (german.ponce@argil.mx)
##############################################################################
from odoo import api, fields, models, _, tools, release
from datetime import datetime
import time
from odoo import SUPERUSER_ID
import time
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import float_compare, float_round

import time
import odoo.addons.decimal_precision as dp
from datetime import date, datetime, timedelta
import time
import pytz

import logging
_logger = logging.getLogger(__name__)

class tms_waybill(models.Model):
    _name = 'tms.waybill'
    _inherit ='tms.waybill'

    cancel_move_id = fields.Many2one('account.move','Poliza de Cancelacion',
        help='Esta Poliza permite cancelar la Factura sin eliminar la Poliza Original.', copy=False )

    original_move_id = fields.Many2one('account.move','Poliza Cancelada',
        help='Esta Poliza hace referencia a la Poliza original de la Factura.', copy=False )


    @api.multi
    def action_confirm(self):
        xparam = self.env['ir.config_parameter'].get_param('tms_create_account_move_for_waybills')[0]
        if xparam == "1":
            move_obj = self.env['account.move']
            account_jrnl_obj=self.env['account.journal']
            cur_obj = self.env['res.currency']
            precision = self.env['decimal.precision'].precision_get('Account')
            period_obj = self.env['account.period']
            if not self[0].journal_id:
                raise ValidationError(_('Error !!!\nYou have not defined Waybill Journal...'))
            for waybill in self:
                journal_id = waybill.journal_id
                company_currency = waybill.company_id.currency_id
                if waybill.amount_untaxed <= 0.0:
                    raise ValidationError(_('Warning !!!\nCould not Confirm this Waybill ! Total Amount must be greater than zero.'))
                elif not waybill.travel_id:
                    raise ValidationError(_('Warning !!!\nCould not Confirm this Waybill ! Waybill must be assigned to a Travel before confirming.'))
                move_lines = []
                notes = _("Waybill: %s\nTravel: %s\nDriver: (%s) %s\nVehicle: %s") % \
                        (waybill.name, waybill.travel_id.name, waybill.travel_id.employee_id.id, 
                         waybill.travel_id.employee_id.name, waybill.travel_id.vehicle_id.name)

                for waybill_line in waybill.waybill_line_ids:
                    if waybill_line.line_type != "product":
                        continue
                    if not ((waybill_line.product_id.tms_property_account_income_id.id or \
                             waybill_line.product_id.categ_id.tms_property_account_income_categ_id.id) or \
                            (waybill_line.product_id.tms_property_account_income_id2.id or \
                             waybill_line.product_id.categ_id.tms_property_account_income_categ_id2.id)):
                        raise ValidationError(_('Error !!!\nYou have not defined Waybill Accounts for product %s') % 
                                        (waybill_line.product_id.name))
                    period_id = False
                    if waybill.cancel_move_id:
                        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        start = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
                        user = self.env.user
                        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
                        start = pytz.utc.localize(start).astimezone(tz)     
                        tz_date = start.strftime("%Y-%m-%d")
                        period_id = period_obj.search([('date_start', '<=', tz_date),('date_stop','>=', tz_date), ('state','=','draft')])
                        date_to_move = tz_date

                    monto = waybill.currency_id.with_context(date=waybill.date_order).compute(waybill_line.price_subtotal, 
                                                                                              company_currency)
                    
                    debit_vals = waybill.get_move_line_dict(waybill_line, monto, precision, is_debit=True)

                    if period_id:
                        debit_vals.update({
                                                'period_id'  : period_id[0].id,
                                            })
                    move_lines.append((0,0, debit_vals))
                    credit_vals  =  waybill.get_move_line_dict(waybill_line, monto, precision, is_credit=True)
                    if period_id:
                        credit_vals.update({
                                                'period_id'  : period_id[0].id,
                                            })

                    move_lines.append((0,0, credit_vals))
                vals_move = waybill.get_move_dict(notes, move_lines)
                if period_id:
                        vals_move.update({
                                                'date'       : date_to_move,
                                                'period_id'  : period_id[0].id,
                                            })
                move_id = move_obj.create(vals_move)
                move_id.post()
                waybill.write({'move_id': move_id.id})
                            
        self.write({'state':'confirmed'})
        return True


class tms_waybill_cancel(models.TransientModel):
    _name = 'tms.waybill.cancel'
    _inherit ='tms.waybill.cancel'

    date_cancel_move = fields.Date('Fecha de Poliza Cancelacion',
            help='Define la fecha con la cual se creara la Poliza de Cancelacion.', default=fields.Date.today())


    @api.multi
    def cancel_waybill(self):

        """
             To copy Waybills when cancelling them
             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param context: A standard dictionary
             @return : retrun view of Invoice
        """

        waybill_ids =  self._context.get('active_ids',[])
        period_obj = self.env['account.period']
        account_move = self.env['account.move']
        cr = self.env.cr
        if waybill_ids:
            for record in self:                
                for waybill in self.env['tms.waybill'].browse(waybill_ids):
                    self_br = waybill
                    if waybill.invoiced and waybill.invoice_paid:
                        raise ValidationError(_('Warning !!!\nCould not cancel Waybill %s! This Waybill\'s Invoice is already paid') % (waybill.name))
                    elif waybill.invoiced and waybill.invoice_id and waybill.invoice_id.id and waybill.invoice_id.state != 'cancel': #and waybill.billing_policy=='manual':
                        raise ValidationError(_('Warning !!!\nCould not cancel Waybill %s! This Waybill is already Invoiced') % (waybill.name))
                    elif waybill.waybill_type=='outsourced' and waybill.supplier_invoiced and waybill.supplier_invoice_paid:
                        raise ValidationError(_('Warning !!!\nCould not cancel Waybill %s! This Waybill\'s Supplier Invoice is already paid') % (waybill.name))
                    #elif waybill.billing_policy=='automatic' and waybill.invoiced and not waybill.invoice_paid:
                    #    waybill.invoice_id
                    #    workflow.trg_validate(self._uid, 'account.invoice', waybill.invoice_id.id, 'cancel', self._cr)
                    #    waybill.invoice_id.unlink()
                    elif waybill.waybill_type=='outsourced' and waybill.supplier_invoiced:
                        raise ValidationError(_('Warning !!!\nCould not cancel Waybill %s! This Waybill\'s Supplier Invoice is already created. First, cancel Supplier Invoice and then try again') % (waybill.name))
                    if waybill.move_id.id:
                        if waybill.move_id.state != 'draft':
                            waybill.move_id.button_cancel()
                        if self_br.cancel_move_id and self_br.original_move_id:
                            move_list = [self_br.original_move_id.id,self_br.cancel_move_id.id]
                            waybill.message_post(body=_("Historico de Polizas de Cancelacion.<br/>Polizas con los IDS: <em>%s</em> Fecha <b>%s</b>.") % (str(move_list), fields.Date.today()))

                        period_invoice_id = period_obj.search([('date_start', '<=', waybill.date_order),('date_stop','>=', waybill.date_order),('special','=',False)])
                        date_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        start = datetime.strptime(date_now, "%Y-%m-%d %H:%M:%S")
                        user = self.env.user
                        tz = pytz.timezone(user.tz) if user.tz else pytz.utc
                        start = pytz.utc.localize(start).astimezone(tz)     
                        tz_date = start.strftime("%Y-%m-%d")
                        ### tz_date es la fecha correcta con la zona hroaria

                        period_cancel_id = period_obj.search([('date_start', '<=', tz_date),('date_stop','>=', tz_date),('special','=',False)])
                        if period_invoice_id == period_cancel_id:
                            move_obj = self.env['account.move']
                            if waybill.move_id.state != 'draft':
                                move_id.button_cancel()
                            waybill.move_id.unlink()
                        else:
                            cp_name = self_br.name if self_br.name else ""
                            original_move_id=self_br.move_id.id
                            original_move_period = self_br.move_id.period_id
                            self_br.move_id.write(
                                {'name':self_br.move_id.name+" (C)"})
                            name_move_cancelation = self_br.move_id.name+" (Poliza de Cancelacion)"
                            #cr.execute("update tms_waybill set move_id=null where id=%s" % ids[0])
                            self_br.write({'original_move_id':original_move_id})
                            ########## Periodo para la Poliza de Cancelacion #########
                            period_to_reopen = False
                            if original_move_period.state == 'done':
                                original_move_period.action_draft()
                                period_to_reopen = True
                            ###### Poliza de Cancelacion ######
                            cancel_move_id = account_move.browse(original_move_id).copy(default={'ref':self_br.name})
                            if record.date_cancel_move:
                                period_obj = self.env['account.period']
                                period_to_move = period_obj.search([('date_start', '<=', record.date_cancel_move),('date_stop','>=', record.date_cancel_move),('special','=',False)])
                                cancel_move_id.write(
                                    {
                                    'ref':self_br.name,
                                    'period_id': period_to_move[0].id if period_to_move else original_move_period.id,
                                    'date': record.date_cancel_move,
                                    })
                            else:
                                cancel_move_id.write(
                                {
                                'ref':self_br.name,
                                'period_id': original_move_period.id,
                                })
                            self_br.write({'cancel_move_id':cancel_move_id.id})

                            cr.execute("""
                                update account_move_line
                                    set partner_id = %s
                                    where move_id in %s
                                """, (waybill.partner_id.id,tuple([original_move_id,cancel_move_id.id]),))

                            for m_cancelation in [cancel_move_id]:
                                m_cancelation.write({'name':name_move_cancelation})
                                for mcline in m_cancelation.line_ids:
                                    if mcline.debit:
                                        debit = mcline.debit
                                        amount_currency = 0.0
                                        if mcline.amount_currency:
                                            if mcline.amount_currency > 0:
                                                amount_currency = mcline.amount_currency * -1
                                            else:
                                                amount_currency = mcline.amount_currency
                                        mcline.write({
                                            'amount_currency': amount_currency,
                                            'debit': 0.0,
                                            'credit': debit,
                                            })
                                    elif mcline.credit:
                                        amount_currency = 0.0
                                        if mcline.amount_currency:
                                            if mcline.amount_currency < 0:
                                                amount_currency = abs(mcline.amount_currency)
                                            else:
                                                amount_currency = mcline.amount_currency
                                        credit = mcline.credit
                                        mcline.write({
                                            'amount_currency': amount_currency,
                                            'credit': 0.0,
                                            'debit': credit,
                                            })
                            cancel_move_id.sudo().action_post()
                            account_move.browse(original_move_id).sudo().action_post()
                            #### Cerrando el Periodo Afectado #####
                            if period_to_reopen == True:
                                account_period = self.env['account.period.close']
                                ctx_w = {}
                                ctx_w.update({
                                    'active_id':original_move_period.id,
                                    'active_ids': [original_move_period.id],
                                    'active_model': 'account.period',
                                    })
                                account_period_id = account_period.with_context(ctx_w).create(
                                    {'sure':True})
                                account_period_id.with_context(ctx_w).date_save()

                        #waybill.move_id.unlink()
                    waybill.write({'move_id' : False, 'state':'cancel', 'cancelled_by':self.env.user.id,'date_cancelled': fields.Date.today()})
                    if record.copy_waybill:
                        default ={} 
                        default.update({'replaced_waybill_id': waybill.id,'move_id':False })
                        if record.sequence_id.id:
                            default.update({'sequence_id': record.sequence_id.id })
                        if record.date_order:
                            default.update({'date_order': record.date_order })
                        waybill2 = waybill.copy(default=default)
        return {'type': 'ir.actions.act_window_close'}