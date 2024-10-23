# -*- encoding: utf-8 -*-
### <German Ponce Dominguez>

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

class TmsTipoUnidad(models.Model):
    _name = 'tms.tipo.unidad'
    _description = 'Tipos de Unidades'
    
    name = fields.Char('Descripción', size=128, required=True)


class TMSTravel(models.Model):
    _name = 'tms.travel'
    _inherit ='tms.travel'

    tipo_unidad_id = fields.Many2one('tms.tipo.unidad', 'Tipo de Unidad')
    tipo_servicio = fields.Selection([('publico','Público'),('privado','Privado')], 'Tipo de Servicio',
    								  default="publico")