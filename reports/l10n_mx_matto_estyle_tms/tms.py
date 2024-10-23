# -*- encoding: utf-8 -*-
### <German Ponce Dominguez>

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError


class FleetMroOrderTask(models.Model):
    _inherit ='fleet.mro.order.task'


    def get_groupped_partners(self, purchase_order_line_ids):
        partners = []
        if not purchase_order_line_ids:
            return []
        for line in purchase_order_line_ids:
            if line.order_id.partner_id not in partners:
                partners.append(line.order_id.partner_id) 
        return partners

    def get_groupped_costs(self, purchase_order_line_ids):
        cost_total = 0.0
        for line in purchase_order_line_ids:
           cost_total += line.price_total
        return cost_total

class StockMove(models.Model):
    _name = 'stock.move'
    _inherit ='stock.move'

    @api.multi
    def get_move_destiny_return(self, move_br):
        return_list = False
        origin_returned_move_ids = self.search([('origin_returned_move_id','=',move_br.id)])
        if origin_returned_move_ids:
            return_list = origin_returned_move_ids
        return return_list
