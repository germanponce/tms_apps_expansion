# -*- coding: utf-8 -*-

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



# TMS Travel Expenses
class tms_expense(models.Model):
    _inherit = 'tms.expense'


    @api.multi
    def compute_special_amounts_expenses(self):
        factor_special = self.env['tms.factor.special'].search([('type', '=', 'retention'), ('active', '=', True)], limit=1)

        expense_line_obj = self.env['tms.expense.line']


        resx = expense_line_obj.search([('expense_id', 'in', self._ids),
                                        ('control','=', 1),
                                        #('travel_id','!=',False),
                                        ('loan_id','=',False)
                                       ])   
        if resx:
            res = resx.with_context({'control': True}).unlink()
        for expense in self:
            if factor_special:
                exec(factor_special.python_code)

            # exp_invoice = self.env['tms.expense.invoice']
            # exp_invoice.create_account_move(expense.id)

        return True


    @api.multi
    def action_approve(self):
        self.compute_special_amounts_expenses()
        res = super(tms_expense, self).action_approve()
        return res

    @api.multi
    def action_confirm(self):
        self.compute_special_amounts_expenses()
        res = super(tms_expense, self).action_confirm()
        return res