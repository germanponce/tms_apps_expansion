# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Argil Consulting (<http://www.argil.mx>)
#    Information:
#    Israel Cruz Argil  - israel.cruz@argil.mx
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

from odoo import api, fields, models, _, tools, release
from datetime import datetime
import time
from odoo import SUPERUSER_ID
import time
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import float_compare, float_round



class tms_waybill(models.Model):
    _inherit = "tms.waybill"

    amount_untaxed_company_currency = fields.Float(
                                'SubTotal MXN', compute='_get_untaxed_amount_in_company_currency',
                                digits=(14,2), store=True,)
    
    def _get_untaxed_amount_in_company_currency(self):
        for waybill in self:
            currency_obj = self.env['res.currency']
            amount = waybill.amount_untaxed
            if waybill.currency_id.id != waybill.company_id.currency_id.id:
                currency_id = waybill.currency_id
                amount = currency_id._convert(waybill.amount_untaxed, waybill.company_id.currency_id, waybill.company_id, waybill.date_waybill or fields.Date.today())

            waybill.amount_untaxed_company_currency = amount


        

##############################
# tms.waybill.line
##############################
class tms_waybill_line(models.Model):
    _inherit = "tms.waybill.line"

    amount_untaxed_company_currency = fields.Float(
                                'SubTotal MXN', compute='_get_untaxed_amount_in_company_currency',
                                digits=(14,2), store=True,)
    
    def _get_untaxed_amount_in_company_currency(self):
        for waybill in self:
            currency_obj = self.env['res.currency']
            amount = waybill.price_subtotal
            if waybill.waybill_id:
                if waybill.waybill_id.currency_id.id != waybill.waybill_id.company_id.currency_id.id:
                    currency_id = waybill.waybill_id.currency_id
                    amount = currency_id._convert(waybill.price_subtotal, waybill.company_id.currency_id, waybill.company_id, waybill.date_waybill or fields.Date.today())

            waybill.amount_untaxed_company_currency = amount



class tms_waybill_analysis(models.Model):
    _name = 'tms.waybill.analysis'
    _inherit ='tms.waybill.analysis'
    

    amount_untaxed_company_currency = fields.Float(
                                'SubTotal MXN',
                                digits=(14,2))

    argil_sql_str = """
        create or replace view tms_waybill_analysis as
        select row_number() over() as id,
        a.store_id, a.waybill_category, a.sequence_id,
        a.name, 
        a.date_order,
        a.partner_id, a.travel_id, d.employee_id, d.vehicle_id, d.trailer1_id, d.dolly_id, d.trailer2_id,
        d.route_id, e.departure_id, e.arrival_id,
        a.currency_id, a.waybill_type, a.invoice_id, a.invoice_name, a.user_id, prod_tmpl.tms_category, b.product_id, 
        d.framework, 
        f.product_id as shipped_product_id,
        sum(f.product_uom_qty) / 
        (case (select count(id) from tms_waybill_line where waybill_id=a.id)::FLOAT
        when 0.0 then 1
        else (select count(id) from tms_waybill_line where waybill_id=a.id)::FLOAT
        end)
        qty,
        sum(b.price_subtotal) / 
        (case (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
        when 0.0 then 1
        else (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
        end)
         amount,
        sum(b.amount_untaxed_company_currency) / 
        (case (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
        when 0.0 then 1
        else (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
        end)
         amount_untaxed_company_currency,

         a.operation_id

        from tms_waybill a
            left join tms_waybill_line b on (b.waybill_id = a.id and b.line_type = 'product')
            left join product_product c on (c.id = b.product_id)
            inner join product_template prod_tmpl on prod_tmpl.id=c.product_tmpl_id
            left join tms_travel d on (a.travel_id = d.id)
            left join fleet_vehicle fv on (d.vehicle_id = fv.id)
            left join tms_route e on (d.route_id = e.id)
            left join tms_waybill_shipped_product f on (f.waybill_id = a.id)
        group by a.id, c.id, a.store_id, a.sequence_id,
        a.name, a.date_order, 
        a.partner_id, a.travel_id, d.employee_id, d.vehicle_id, fv.name, d.trailer1_id, d.dolly_id, d.trailer2_id,
        d.route_id, e.departure_id, e.arrival_id,
        a.currency_id, a.waybill_type, a.invoice_id, a.invoice_name, a.user_id, prod_tmpl.tms_category, b.product_id, 
        d.framework, b.price_subtotal, f.product_id
        --order by a.store_id, a.date_order, a.name
        ;
        """

    

    @api.model_cr
    def init(self):
        # self._table = tms_waybill_analysis
        tools.drop_view_if_exists(self.env.cr, self._table)        
        self.env.cr.execute(self.argil_sql_str)



# ##############################
# # tms.waybill.analysis
# ##############################
# class tms_waybill_analysis(osv.osv):
#     _inherit = "tms.waybill.analysis"


#     _columns = {
#         'amount_untaxed_company_currency' : fields.float('Monto MXN', 
#                                                          digits_compute=dp.get_precision('Sale Price'), readonly=True),

#         }

    
#     def init(self, cr):
#         tools.sql.drop_view_if_exists(cr, 'tms_waybill_analysis')
#         cr.execute("""

# create or replace view tms_waybill_analysis as
# select row_number() over() as id,
# a.shop_id, a.waybill_category, a.sequence_id,
# a.state, a.name, 
# date_order,
# --date_trunc('day', a.date_order) as date_order,
# to_char(date_trunc('day',a.date_order), 'YYYY') as year,
# to_char(date_trunc('day',a.date_order), 'MM') as month,
# to_char(date_trunc('day',a.date_order), 'YYYY-MM-DD') as day,
# a.partner_id, a.travel_id, d.employee_id, d.unit_id, fv.name as unit_char, d.trailer1_id, d.dolly_id, d.trailer2_id,
# d.route_id, e.departure_id, e.arrival_id,
# a.currency_id, a.waybill_type, a.invoice_id, a.invoice_name, a.user_id, c.tms_category, b.product_id, 
# d.framework, 
# f.product_id as shipped_product_id,
# sum(f.product_uom_qty) / 
# (case (select count(id) from tms_waybill_line where waybill_id=a.id)::FLOAT
# when 0.0 then 1
# else (select count(id) from tms_waybill_line where waybill_id=a.id)::FLOAT
# end)
# qty,
# sum(b.price_subtotal) / 
# (case (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
# when 0.0 then 1
# else (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
# end)
#  amount,
# sum(b.amount_untaxed_company_currency) / 
# (case (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
# when 0.0 then 1
# else (select count(id) from tms_waybill_shipped_product where waybill_id=a.id)::FLOAT
# end)
#  amount_untaxed_company_currency,
#  a.operation_id

# from tms_waybill a
# 	left join tms_waybill_line b on (b.waybill_id = a.id and b.line_type = 'product')
# 	left join product_product c on (c.id = b.product_id)
# 	left join tms_travel d on (a.travel_id = d.id)
#     left join fleet_vehicle fv on (d.unit_id = fv.id)
# 	left join tms_route e on (d.route_id = e.id)
# 	left join tms_waybill_shipped_product f on (f.waybill_id = a.id)
# group by a.id, c.id, a.shop_id, a.sequence_id,
# a.state, a.name, a.date_order, 
# a.partner_id, a.travel_id, d.employee_id, d.unit_id, fv.name, d.trailer1_id, d.dolly_id, d.trailer2_id,
# d.route_id, e.departure_id, e.arrival_id,
# a.currency_id, a.waybill_type, a.invoice_id, a.invoice_name, a.user_id, c.tms_category, b.product_id, 
# d.framework, b.price_subtotal, f.product_id
# order by a.shop_id, a.date_order, a.name

# ;
#         """)
    
    
    
    
# ##############################
# # tms.travel.analysis
# ##############################
# class tms_travel_analysis(osv.osv):
#     _inherit = "tms.travel.analysis"


#     _columns = {
#         'amount_untaxed_company_currency' : fields.float('Monto MXN', 
#                                                          digits_compute=dp.get_precision('Sale Price'), readonly=True),

#         }
    
#     def init(self, cr):
#         tools.sql.drop_view_if_exists(cr, 'tms_travel_analysis')
#         cr.execute ("""
# CREATE OR REPLACE VIEW tms_travel_analysis as
# select row_number() over() as id,
# a.shop_id, a.name, 

# a.date,
# to_char(date_trunc('day',a.date), 'YYYY') as year,
# to_char(date_trunc('day',a.date), 'MM') as month,
# to_char(date_trunc('day',a.date), 'YYYY-MM-DD') as day,

# a.state, a.employee_id, a.framework, f.unit_type_id, 
# a.unit_id, f.name as unit_char, a.trailer1_id, a.dolly_id, a.trailer2_id, a.route_id, a.departure_id departure, a.arrival_id arrival,
# b.id as waybill_id, b.date_order as waybill_date, 
# case 
# when b.partner_id is null then 1
# else b.partner_id
# end partner_id, 
# b.state as waybill_state, b.sequence_id as waybill_sequence, b.currency_id, b.waybill_type, b.invoice_id, b.invoice_name, b.user_id,
# c.product_id, 
# c.price_subtotal / 
# (case (select count(id) from tms_waybill_shipped_product where waybill_id=b.id)::FLOAT
# when 0.0 then 1.0 
# else (select count(id) from tms_waybill_shipped_product where waybill_id=b.id)::FLOAT
# end) as amount,

# c.amount_untaxed_company_currency / 
# (case (select count(id) from tms_waybill_shipped_product where waybill_id=b.id)::FLOAT
# when 0.0 then 1.0 
# else (select count(id) from tms_waybill_shipped_product where waybill_id=b.id)::FLOAT
# end) as amount_untaxed_company_currency,


# d.tms_category, e.product_id as shipped_product_id, 
# e.product_uom_qty / 
# (case (select count(id) from tms_waybill_line where waybill_id=b.id)::FLOAT
# when 0.0 then 1
# else (select count(id) from tms_waybill_line where waybill_id=b.id)::FLOAT
# end) as qty,
# a.operation_id
# from tms_travel a
# 	left join tms_waybill b on (a.id = b.travel_id and b.state in ('approved', 'confirmed'))	
# 	left join tms_waybill_line c on (c.waybill_id = b.id and c.line_type = 'product')
# 	left join product_product d on (c.product_id = d.id)
# 	left join tms_waybill_shipped_product e on (e.waybill_id = b.id)
# 	left join fleet_vehicle f on (a.unit_id = f.id)
# order by a.shop_id, a.name, a.date;
#         """)