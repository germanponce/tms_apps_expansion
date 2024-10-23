# -*- coding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

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


class PurchaseRequisition(models.Model):
    _name = 'purchase.requisition'
    _inherit ='purchase.requisition'

    def _get_department_id(self):
        department_id = False
        hr_employee = self.env['hr.employee']
        employee_rel = hr_employee.search([('user_id','=',self.env.user.id)], limit=1)
        if employee_rel:
            if employee_rel.department_id:
                department_id = employee_rel.department_id.id
        return department_id

    department_id = fields.Many2one('hr.department', 'Departamento', default=_get_department_id)

    type_of_agreement = fields.Selection([('standard','Estandar'),
                                          ('mro','Mantenimiento'),
                                          ('supplies','Insumos'),
                                          ], 
                                        string='Tipo de Acuerdo',
                                        copy=False)

    @api.multi
    def action_in_progress(self):
        self.ensure_one()
        if not all(obj.line_ids for obj in self):
            raise UserError("No se puede confirmar acuerdos '%s' porque no existen líneas de productos." % self.name) 
        if self.type_id.quantity_copy == 'none' and self.vendor_id:
            for requisition_line in self.line_ids:
                if requisition_line.price_unit <= 0.0:
                    raise UserError('No se puede confirmar el Acuerdo Abierto sin precio.')
                if requisition_line.product_qty <= 0.0:
                    raise UserError('No se puede confirmar el Acuerdo Abierto sin cantidad')
        sequence_name = ""
        if self.name == 'New':
            if self.type_of_agreement == 'standard':
                if self.is_quantity_copy != 'none':
                    sequence_name = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.tender')
                else:
                    sequence_name = self.env['ir.sequence'].next_by_code('purchase.requisition.blanket.order')
            elif self.type_of_agreement == 'mro':
                sequence_name = self.env['ir.sequence'].next_by_code('purchase.requisition.mro')
            elif self.type_of_agreement == 'supplies':
                sequence_name = self.env['ir.sequence'].next_by_code('purchase.requisition.supplies')
            else:
                _logger.warning("\n#### Ocurrio un error al Asignar la Secuencia en el Acuerdo ID %s " % self.id)
        if sequence_name:
            self.name = sequence_name
        res = super(PurchaseRequisition, self).action_in_progress()
        return res

