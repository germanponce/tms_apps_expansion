# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError



class TMSExpense(models.Model):
    _name = 'tms.expense'
    _inherit ='tms.expense'

    payment_reference = fields.Char('Referencia del Pago', size=256)


class account_register_tms_expense_payments(models.TransientModel):

    _inherit = "account.register.tms_expense_payments"

    payment_reference = fields.Char('Referencia del Pago', size=256)


    @api.multi
    def _prepare_payment_vals(self, expenses):
        res = super(account_register_tms_expense_payments, self)._prepare_payment_vals(expenses)
        for rec in self:
            res.update({
                'payment_reference': rec.payment_reference if rec.payment_reference else '',
            })
        return res

    @api.multi
    def create_payments(self):
        res = super(account_register_tms_expense_payments, self).create_payments()
        active_ids = []
        context = dict(self._context)
        if 'active_ids' in context:
            active_ids = context['active_ids']
            active_model = False
            if 'active_model' in context:
                active_model = context['active_model']
                payment_reference = self.payment_reference
                if payment_reference:
                    obj_br = self.env[str(active_model)].browse(active_ids)
                    obj_br.write({'payment_reference': payment_reference})
        return res


class TMSAdvance(models.Model):
    _name = 'tms.advance'
    _inherit ='tms.advance'

    payment_reference = fields.Char('Referencia del Pago', size=256)


class account_register_tms_advance_payments(models.TransientModel):

    _inherit = "account.register.tms_advance_payments"

    payment_reference = fields.Char('Referencia del Pago', size=256)


    @api.multi
    def _prepare_payment_vals(self, expenses):
        res = super(account_register_tms_advance_payments, self)._prepare_payment_vals(expenses)
        for rec in self:
            res.update({
                'payment_reference': rec.payment_reference if rec.payment_reference else '',
            })
        return res

    @api.multi
    def create_payments(self):
        res = super(account_register_tms_advance_payments, self).create_payments()
        active_ids = []
        context = dict(self._context)
        if 'active_ids' in context:
            active_ids = context['active_ids']
            active_model = False
            if 'active_model' in context:
                active_model = context['active_model']
                payment_reference = self.payment_reference
                if payment_reference:
                    obj_br = self.env[str(active_model)].browse(active_ids)
                    obj_br.write({'payment_reference': payment_reference})
        return res
