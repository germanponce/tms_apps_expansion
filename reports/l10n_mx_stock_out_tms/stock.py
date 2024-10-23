# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields



class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit ='stock.picking'

    # supervisor_mechanic_id  = fields.Many2one('hr.employee', 'Encargado', help='Nombre de quien  Aparecera en las Firmas del Documento', )

    mro_mechanic_id  = fields.Many2one('hr.employee', 'Mecanico', help='Nombre de quien  Aparecera en las Firmas del Documento', )