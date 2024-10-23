# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


    

class account_register_tms_advance_payments(models.TransientModel):
    _name = "account.register.tms_advance_payments"
    _inherit = 'account.register.tms_advance_payments'

    hold_diference = fields.Boolean('Mantener la Diferencia', help='Si se desmarca este campo la Diferencia ya no sera tomada en cuenta en la Poliza.', )
    payment_extra_amount = fields.Float('Monto Extra')
    amount3  = fields.Float('Monto Pago Salvado')

    @api.onchange('amount','amount2')
    def onchange_extra_amounts_computing(self):
        if self.amount > self.amount2:
            self.payment_difference = self.amount - self.amount2
            self.amount3 = self.amount
            self.hold_diference = True
            self.payment_extra_amount = self.amount - self.amount2
            self.amount = self.amount2
        else:
            if not self.payment_extra_amount:
                self.payment_difference = 0.0
            else:
                if self.amount3 <= self.amount2:
                    self.payment_difference = 0.0
                    self.payment_extra_amount = 0.0
                else:
                    self.payment_difference = self.amount - self.amount3
                    self.payment_extra_amount = self.amount - self.amount3


    @api.onchange('hold_diference')
    def onchange_hold_diference(self):
        if not self.hold_diference and self.amount3:
            self.payment_difference = 0.0
            self.payment_extra_amount = 0.0
            self.amount3 = 0.0
        if self.payment_extra_amount:
            self.payment_difference = self.payment_extra_amount
    
    @api.multi
    def create_payments(self):
        res = super(account_register_tms_advance_payments, self).create_payments()
        # # if self.amount > self.amount2:
        # #     raise ValidationError(_('Warning !\nYou can not pay more than sum of Travel Advances'))
        # Payment = self.env['account.payment']
        # payments = Payment
        # for payment_vals in self.get_payments_vals():
        #     payments += Payment.create(payment_vals)
        # payments.post_tms_advances()
        for rec in self:
            if rec.payment_difference:
                vals = rec.get_payments_vals()
                print ("#### VALS >>>>>>>> ",vals)
        return res

    # @api.onchange('payment_extra_amount')
    # def onchange_compute_extra_amounts(self):
    #     if self.payment_extra_amount:
    #         self.payment_difference = self.payment_extra_amount




    # @api.multi
    # def _prepare_payment_vals_2(self, advances):
    #     print ("########## ADVANCES >>>>>>>> ",advances)
    #     amount = self._compute_payment_amount(advances=advances) or self.amount2 if self.multi else self.amount2
    #     payment_type = 'outbound'
    #     bank_account = self.partner_bank_account_id
    #     pmt_communication = self.show_communication_field and self.communication \
    #                         or ' '.join([adv.name for adv in advances]) 
        
    #     new_rec = {
    #         'journal_id': self.journal_id.id,
    #         'payment_method_id': self.payment_method_id.id,
    #         'payment_date': self.payment_date,
    #         'communication': pmt_communication,
    #         'tms_advance_ids': [(6, 0, advances.ids)],
    #         'payment_type': payment_type,
    #         'amount': abs(amount),
    #         'currency_id': self.currency_id.id,
    #         'partner_id': advances[0].employee_id.address_home_id.id,
    #         'partner_type': 'supplier',
    #         'partner_bank_account_id': bank_account.id,
    #         'multi': False,
    #     }
    #     return new_rec

    
    # @api.multi
    # def get_payments_vals_2(self):
    #     if self.multi:
    #         groups = self._groupby_advances()
    #         return [self._prepare_payment_vals_2(advances) for advance in groups.values()]
    #     return [self._prepare_payment_vals_2(self.tms_advance_ids)]
    


    # @api.multi
    # def create_payments(self):
    #     if self.amount > self.amount2:
    #         Payment = self.env['account.payment']
    #         payments = Payment
    #         for payment_vals in self.get_payments_vals_2():
    #             payments += Payment.create(payment_vals)
    #         payments.post_tms_advances()
    #     else:
    #         Payment = self.env['account.payment']
    #         payments = Payment
    #         for payment_vals in self.get_payments_vals():
    #             payments += Payment.create(payment_vals)
    #         payments.post_tms_advances()

    #     action_vals = {
    #         'name': _('Payments'),
    #         'domain': [('id', 'in', payments.ids), ('state', '=', 'posted')],
    #         'view_type': 'form',
    #         'res_model': 'account.payment',
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #     }
    #     if len(payments) == 1:
    #         action_vals.update({'res_id': payments[0].id, 'view_mode': 'form'})
    #     else:
    #         action_vals['view_mode'] = 'tree,form'
    #     return action_vals



    