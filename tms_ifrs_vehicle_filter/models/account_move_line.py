
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    def _query_get2(self):
        query = super(AccountMoveLine, self)._query_get2()
        context = self.env.context.copy()
        ### Validamos el Contexto del Reporte, Si tiene Unidades a Filtrar entramos a modificar el query ####
        if context.get('vehicle_ids', False):
            ### El Operador nos permite tener una mineria dinamica para generar el Reporte ####
            if context.get('operator_vehicle',False):
                if context.get('operator_vehicle') == 'vehicle_null':
                    query += " AND l.vehicle_id IS NULL" 
                else:
                    operator_get = context.get('operator_vehicle')
                    query += " AND l.vehicle_id %s (%s)" % (operator_get, ','.join([str(x)  for x in context.get('vehicle_ids')]))
            else:
                ### Si no usa un Operador Dinamico entonces filtramos de manera estandar ###
                query += " AND l.vehicle_id IN (%s)" % ','.join([str(x)  for x in context.get('vehicle_ids')])
        return query