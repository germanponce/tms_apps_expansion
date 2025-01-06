# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools, release

import logging
_logger = logging.getLogger(__name__)

class TMSAnalisisReportsWizard(models.TransientModel):
    """
    batch payment record of customer invoices
    """
    _name = "tms.analisis.reports.wizard"

    def _get_default_company(self):
        return self.env.user.company_id.id

    company_id = fields.Many2one('res.company','Compañía', default=_get_default_company)


    def tms_expense_analysis(self):
        self.env['tms.expense.analysis'].create_temp_view(self.company_id.id)
        list_ids = self.env['tms.expense.analysis'].search([]).ids
        
        return {
            'domain': [('id', 'in', list_ids)],
            'name': "Proyección de Pagos",
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'tms_analysis.view_tms_expense_analysis_tree', 'search_default_this_month':1},
            'res_model': 'tms.expense.analysis',
            'type': 'ir.actions.act_window'

            }
                