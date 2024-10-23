# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
#from pytz import timezone
#import pytz
import time
import logging
_logger = logging.getLogger(__name__)


class FleetMroOrder(models.Model):
    _inherit = 'fleet.mro.order'


    date_start          = fields.Datetime(string='Fecha Inicio Estimada', required=False, 
                                           default=fields.Datetime.now,
                                           track_visibility='onchange', readonly=True, 
                                           states={'draft':[('required',False),('readonly',False)],
                                                  'scheduled':[('required',True),('readonly',False)],
                                                  'check_in':[('required',True),('readonly',False)],
                                                  'revision':[('required',True),('readonly',False)],
                                                  'waiting_approval':[('required',True),('readonly',False)],
                                                  'open':[('required',True),('readonly',False)]})
    date                = fields.Datetime(string='Fecha', readonly=True, default=fields.Datetime.now,
                                           states={'draft':[('readonly',False)],'scheduled':[('readonly',False)],
                                                   'check_in':[('readonly',False)],'revision':[('readonly',False)],
                                                   'waiting_approval':[('readonly',False)]}, 
                                          track_visibility='onchange', required=True)