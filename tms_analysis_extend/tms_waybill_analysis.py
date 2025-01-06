# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools, release
import odoo.addons.decimal_precision as dp

class tms_waybill_analysis(models.Model):
    _name = "tms.waybill.analysis"
    _description = "Waybill Analisys"
    _auto = False
    
    store_id         = fields.Many2one('res.store', string='Sucursal', readonly=True)
    waybill_category  = fields.Many2one('tms.waybill.category', string='Waybill Categ', readonly=True)
    sequence_id       = fields.Many2one('ir.sequence', string='Sequence', readonly=True)

    name              = fields.Char(string='Waybill', size=64, readonly=True)
    date_order        = fields.Date(string='Date', readonly=True)

    partner_id        = fields.Many2one('res.partner', string='Customer', readonly=True)
    travel_id         = fields.Many2one('tms.travel', string='Travel', readonly=True)
    employee_id       = fields.Many2one('hr.employee', string='Driver', readonly=True)
    vehicle_id           = fields.Many2one('fleet.vehicle', string='Unit', readonly=True)
    trailer1_id       = fields.Many2one('fleet.vehicle', string='Trailer 1', readonly=True)
    dolly_id          = fields.Many2one('fleet.vehicle', string='Dolly', readonly=True)
    trailer2_id       = fields.Many2one('fleet.vehicle', string='Trailer 2', readonly=True)
    route_id          = fields.Many2one('tms.route', string='Route', readonly=True)
    departure_id      = fields.Many2one('tms.place', string='Departure', readonly=True)
    arrival_id        = fields.Many2one('tms.place', string='Arrival', readonly=True)
    currency_id       = fields.Many2one('res.currency', string='Currency', readonly=True)
    waybill_type      = fields.Selection([
                                ('Self', 'Self'),
                                ('outsourced', 'Outsourced'),
                                ], string='Waybill Type', readonly=True)
    invoice_id        = fields.Many2one('account.invoice', string='Invoice', readonly=True)
    invoice_name      = fields.Char(string='Invoice Reference',   size=64, readonly=True)
    user_id           = fields.Many2one('res.users', string='Salesman', readonly=True)
    tms_category      = fields.Selection([
                                      ('freight','Freight'), 
                                      ('move','Move'), 
                                      ('insurance','Insurance'), 
                                      ('highway_tolls','Highway Tolls'), 
                                      ('other','Other'),
                                        ], string="Income Category", readonly=True)

    product_id        = fields.Many2one('product.product', string='Product', readonly=True)
    framework         = fields.Char(string='Framework', size=64, readonly=True)
    shipped_product_id= fields.Many2one('product.product', string='Shipped Product', readonly=True)
    qty               = fields.Float(string='Shipped Product Qty', digits=(18,4), readonly=True)
    amount            = fields.Monetary(string='Amount', readonly=True)
    operation_id      = fields.Many2one('tms.operation', string='Operation', readonly=True)

    amount_untaxed_company_currency = fields.Float(
                                'SubTotal MXN',
                                digits=(14,2))

    def create_temp_view(self, company_id=False):
        self.invalidate_cache()
        tools.drop_view_if_exists(self.env.cr, self._table)
        print ("#### company_id ", company_id)
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
                     where a.company_id=%s
                    group by a.id, c.id, a.store_id, a.sequence_id,
                    a.name, a.date_order, 
                    a.partner_id, a.travel_id, d.employee_id, d.vehicle_id, fv.name, d.trailer1_id, d.dolly_id, d.trailer2_id,
                    d.route_id, e.departure_id, e.arrival_id,
                    a.currency_id, a.waybill_type, a.invoice_id, a.invoice_name, a.user_id, prod_tmpl.tms_category, b.product_id, 
                    d.framework, b.price_subtotal, f.product_id
                    --order by a.store_id, a.date_order, a.name
                    ;
                    """ % (company_id,)
        self.env.cr.execute(argil_sql_str)


    @api.model_cr
    def init(self):
        _logger.info("\n########### Generando la Vista Analisis de Cartas Porte .............")
        #self.create_temp_view()
            