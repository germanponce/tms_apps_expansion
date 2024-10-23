# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Argil Consulting (<http://www.argil.mx>)
#    Information:
#    Israel Cruz Argil  - israel.cruz@argil.mx
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
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


##############################
# account.payment
##############################

class account_payment(models.Model):
    _inherit = "account.payment"

    amount_untaxed_company_currency = fields.Float(
                                'SubTotal MXN', compute='_get_untaxed_amount_in_company_currency',
                                digits=(14,2), store=True,)
    
    def _get_untaxed_amount_in_company_currency(self):
        for payment in self:
            currency_obj = self.env['res.currency']
            amount = payment.amount
            if payment.currency_id.id != payment.company_id.currency_id.id:
                currency_id = payment.currency_id
                amount = currency_id._convert(payment.amount, payment.company_id.currency_id, payment.company_id, payment.payment_date or fields.Date.today())

            payment.amount_untaxed_company_currency = amount


        



