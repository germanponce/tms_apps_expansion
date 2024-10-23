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


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit ='sale.order'


    quotation_store_id = fields.Many2one('res.store', 'Sucursal', help='Indica la Sucursal de la cual se genera la Cotización', )


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    quotation_store_id = fields.Many2one(related="group_id.sale_id.quotation_store_id", string="Sucursal Cotizacion", store=True, readonly=False,
        help='Sucursal Relacionada con la Cotización', )

