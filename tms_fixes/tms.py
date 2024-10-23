# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields



class tms_fuelvoucher(models.Model):
    _inherit ='tms.fuelvoucher'


    @api.onchange('driver_helper','no_travel')
    def on_change_driver_helper(self):
        if self.no_travel  == False:
            self.employee_id = self.driver_helper and self.employee2_id or self.employee1_id



# TMS Travel Expenses
class tms_expense(models.Model):
    _inherit = 'tms.expense'


    @api.onchange('employee_id_control')
    def on_change_employee_id(self):
        res = self.search([('employee_id', '=', self.employee_id_control.id),('state','in', ('draft','approved'))], limit=1)
        if res:
            raise ValidationError(_('Error !\nYa existe un registro de Liquidación pendiente de ser Confirmada. No puede crear otra Liquidación con el mismo Operador.!!!'))
        
        # Validamos que no cambie el operador, si se equivoco y ya habia seleccionado Operador que descarte y/o Cancele
        if self.employee_id and self.employee_id_control and self.employee_id and self.employee_id_control != self.employee_id:
            raise ValidationError(_('Error !\nNo se permite cambiar al Operador !!!'))
        
        self.employee_id = self.employee_id_control
        
        domain = {}
        domain['travel_ids'] = [('employee_id','=', self.employee_id.id), ('state','=','done')]
        if self.parameter_docs_required == 1:
            domain['travel_ids'] += ['|', ('tms_travel_extra_docs_id','!=', False),
                                     '&', ('advance_count','=',0), 
                                     '&', ('waybill_count','=',0), ('fuelvoucher_count','=',0)]
        return {'domain': domain}
