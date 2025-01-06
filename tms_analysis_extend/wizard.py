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
            'name': "Analisis de Gastos",
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'tms_analysis.view_tms_expense_analysis_tree', 'search_default_this_month':1},
            'res_model': 'tms.expense.analysis',
            'type': 'ir.actions.act_window'

            }

    def tms_waybill_analysis(self):
        self.env['tms.waybill.analysis'].create_temp_view(self.company_id.id)
        list_ids = self.env['tms.waybill.analysis'].search([]).ids
        
        return {
            'domain': [('id', 'in', list_ids)],
            'name': "Analisis de Cartas Porte",
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'tms_analysis.view_tms_travel_analysis_pivot', 'search_default_ended_this_month':1, 'group_by':[], 'group_by_no_leaf':1},
            'res_model': 'tms.expense.analysis',
            'type': 'ir.actions.act_window'

            }
                


#### Ejecutar:
### delete from ir_filters where name in ('Tipo de Gasto','Combustible','Salario del Empleado');
###
###
###