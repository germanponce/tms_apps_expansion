# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import time
import math

from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, exceptions, fields, models, _
from pytz import timezone
import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)



class ResCompany(models.Model):
    _name = 'res.company'
    _inherit ='res.company'

    date_validation_order = fields.Date('Fecha Validez', help='Fecha de Validez para las Cotizaciones.', )

class SaleConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    date_validation_order = fields.Date('Fecha Validez', related='company_id.date_validation_order', help='Fecha de Validez para las Cotizaciones.', readonly=False)

    @api.onchange('quotation_validity_days')
    def _onchange_quotation_validity_days(self):
        if not self.date_validation_order:
            if self.quotation_validity_days <= 0:
                self.quotation_validity_days = self.env['res.company'].default_get(['quotation_validity_days'])['quotation_validity_days']
                return {
                    'warning': {'title': "Warning", 'message': "Quotation Validity is required and must be greater than 0."},
                }

    @api.onchange('date_validation_order')
    def _onchange_date_validation_order(self):
        if str(self.date_validation_order) < str(fields.Date.today()):
            self.date_validation_order = False
            return {
                'warning': {'title': "Error", 'message': "La Fecha no puede ser menor a la actual."},
            }


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit ='sale.order'


    def _default_validity_date(self):
        if self.env.user.company_id.date_validation_order:
            date_validation_order = self.env.user.company_id.date_validation_order
            return date_validation_order
        return False

    validity_date = fields.Date(string='Fecha Validez', readonly=True, copy=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help="Validity date of the quotation, after this date, the customer won't be able to validate the quotation online.", default=_default_validity_date)

