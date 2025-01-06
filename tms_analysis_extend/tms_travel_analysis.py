# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools, release
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

class tms_travel_analysis(models.Model):
    _inherit = "tms.travel.analysis"
    
    store_id = fields.Many2one('res.store', string="Sucursal", readonly=True)

    def create_temp_view(self, company_id=False):
        self.invalidate_cache()
        tools.drop_view_if_exists(self.env.cr, self._table)
        argil_sql_str = """
                    CREATE OR REPLACE VIEW tms_travel_analysis AS (
                        WITH r AS (
                            -- Bloque de ingresos (a-income)
                            SELECT 
                                travel.name, 
                                travel.date, 
                                travel.state, 
                                travel.employee_id, 
                                travel.framework, 
                                travel.store_id,
                                travel.vehicle_id, 
                                vehicle.vehicle_type_id, 
                                vehicle.supplier_vehicle,
                                travel.trailer1_id, 
                                travel.dolly_id, 
                                travel.trailer2_id, 
                                travel.route_id, 
                                route.distance AS route_distance, 
                                odom_read.distance AS real_distance,
                                travel.departure_id, 
                                travel.arrival_id, 
                                travel.travel_template_id, 
                                travel.operation_id,
                                'a-income' AS amount_type, 
                                wb.operation_id AS concept_operation_id, 
                                wb.id AS waybill_id, 
                                wb.sequence_id AS wb_sequence, 
                                wb.travel_template_id AS wb_travel_template_id, 
                                wb.currency_id,
                                wb.date_order AS wb_date, 
                                wb.state AS wb_state, 
                                wb.invoice_id AS wb_invoice_id, 
                                wb.partner_id AS wb_partner_id, 
                                wb_line.product_id, 
                                wb_line.product_uom_qty AS qty, 
                                wb_line.product_uom, 
                                wb_line.price_subtotal AS amount, 
                                NULL::int AS expense_id, 
                                NULL::date AS expense_date,
                                prod_tmpl.tms_category
                            FROM 
                                tms_travel travel
                            INNER JOIN 
                                tms_route route ON route.id = travel.route_id
                            LEFT JOIN 
                                fleet_vehicle_odometer odom_read ON odom_read.travel_id = travel.id AND odom_read.vehicle_id = travel.vehicle_id
                            LEFT JOIN 
                                fleet_vehicle vehicle ON vehicle.id = travel.vehicle_id
                            LEFT JOIN 
                                tms_waybill wb ON wb.travel_id = travel.id AND wb.state = 'confirmed'
                            LEFT JOIN 
                                tms_waybill_line wb_line ON wb_line.waybill_id = wb.id
                            LEFT JOIN 
                                product_product prod ON prod.id = wb_line.product_id
                            LEFT JOIN 
                                product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
                            WHERE 
                                    travel.company_id = %s
                            UNION ALL

                            -- Bloque de gastos (b-expense)
                            SELECT 
                                travel.name, 
                                travel.date, 
                                travel.state, 
                                travel.employee_id, 
                                travel.framework, 
                                travel.store_id,
                                travel.vehicle_id, 
                                vehicle.vehicle_type_id, 
                                vehicle.supplier_vehicle,
                                travel.trailer1_id, 
                                travel.dolly_id, 
                                travel.trailer2_id, 
                                travel.route_id,
                                0.0 AS route_distance, 
                                0.0 AS real_distance,
                                travel.departure_id, 
                                travel.arrival_id, 
                                travel.travel_template_id, 
                                travel.operation_id,
                                'b-expense' AS amount_type, 
                                expense_line.operation_id AS concept_operation_id, 
                                NULL::int AS waybill_id, 
                                NULL::int AS wb_sequence, 
                                NULL::int AS wb_travel_template_id, 
                                expense.currency_id,
                                NULL::date AS wb_date, 
                                ''::char AS wb_state, 
                                NULL::int AS wb_invoice_id, 
                                NULL::int AS wb_partner_id, 
                                expense_line.product_id, 
                                expense_line.product_uom_qty * -1.0 AS qty, 
                                expense_line.product_uom, 
                                expense_line.price_subtotal * -1.0 AS amount, 
                                expense.id AS expense_id, 
                                expense.date AS expense_date,
                                prod_tmpl.tms_category
                            FROM 
                                tms_travel travel
                            LEFT JOIN 
                                fleet_vehicle vehicle ON vehicle.id = travel.vehicle_id
                            INNER JOIN 
                                tms_expense_line expense_line ON expense_line.travel_id = travel.id
                            INNER JOIN 
                                tms_expense expense ON expense.id = expense_line.expense_id
                            INNER JOIN 
                                product_product prod ON prod.id = expense_line.product_id
                            INNER JOIN 
                                product_template prod_tmpl ON prod_tmpl.id = prod.product_tmpl_id
                            WHERE 
                                    travel.company_id = %s
                        ) 
                        SELECT 
                            ROW_NUMBER() OVER() AS id, 
                            * 
                        FROM 
                            r
                    );

                    """ % (company_id, company_id)
        self.env.cr.execute(argil_sql_str)


    @api.model_cr
    def init(self):
        _logger.info("\n########### Generando la Vista Analisis de Cartas Porte .............")
        #self.create_temp_view()
            