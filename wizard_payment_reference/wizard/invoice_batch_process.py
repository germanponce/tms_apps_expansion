# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit ='account.payment'

    payment_reference = fields.Char('Referencia del Pago', size=256, readonly=False)


class AccountRegisterPayments(models.TransientModel):
    """
    Inheritance to make payments in batches
    """
    _inherit = "account.register.payments"

    payment_reference = fields.Char('Referencia del Pago', size=256)

    # -------------------------------------------------------------------------
    # BUSINESS METHODS
    # -------------------------------------------------------------------------

    def _prepare_payment_vals(self, invoices):
        payment_vals = super(AccountRegisterPayments, self)._prepare_payment_vals(invoices=invoices)
        payment_vals.update({
                'payment_reference': self.payment_reference,
            })
        return payment_vals

    # def _create_payment_vals_from_batch(self, batch_result):
    #     print ("###### _create_payment_vals_from_batc >>>>>>>>>>>>>>> ")
    #     batch_values = super(AccountRegisterPayments, self)._create_payment_vals_from_batch()
    #     batch_values.update({
    #             'payment_reference': self.payment_reference,
    #         })
    #     return batch_values