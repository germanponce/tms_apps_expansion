# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo import api, fields, models, _, tools
import odoo.addons.decimal_precision as dp

class tms_expense_analysis(models.Model):
    _name = "tms.expense.analysis"
    _description = "Travel Expenses Analisys"
    _auto = False
    _rec_name = 'name'
    
    driver_helper = fields.Boolean(string='Segundo Operador')
    store_id     = fields.Many2one('res.store', 'Sucursal', readonly=True)
    name          = fields.Char(string='Nombre', size=64, readonly=True)
    date          = fields.Date(string='Fecha', readonly=True)

    year = fields.Char('Año', size=4, readonly=True)
    month = fields.Selection([('01',_('Enero')), ('02',_('Febrero')), ('03',_('Marzo')), ('04',_('Abril')),
                                    ('05',_('Mayo')), ('06',_('Junio')), ('07',_('Julio')), ('08',_('Agosto')), ('09',_('September')),
                                    ('10',_('Octubre')), ('11',_('Noviembre')), ('12',_('Diciembre'))], 'Mes',readonly=True)
    day = fields.Char('Dia', size=128, readonly=True)

    employee_id   = fields.Many2one('hr.employee', string='Operador', readonly=True)
    vehicle_id       = fields.Many2one('fleet.vehicle', string='Vehiculo', readonly=True)
    vehicle_char     = fields.Char(string='Vehicle', size=64, readonly=True)
    currency_id   = fields.Many2one('res.currency', string='Moneda', readonly=True)
    product_id    = fields.Many2one('product.product', string='Producto', readonly=True)
    expense_line_description = fields.Char(string='Descripción Gasto',   size=256, readonly=True)

    travel_id     = fields.Many2one('tms.travel', string='Viaje', readonly=True)
    route_id      = fields.Many2one('tms.route', string='Ruta', readonly=True)
#        waybill_income'= fields.float('Waybill Amount', digits=(18,2), readonly=True)        

#        travels'       = fields.integer('Travels', readonly=True)        
    qty           = fields.Float(string='Cantidad', digits=(18,4), readonly=True)        
    price_unit    = fields.Float(string='Precio Unitario', readonly=True, digits=dp.get_precision('Product Price'))
    subtotal      = fields.Monetary(string='Subtotal', readonly=True)
    operation_id  = fields.Many2one('tms.operation', string='Operacion', readonly=True)

    line_type   = fields.Selection([
                                      ('real_expense','Gasto Real'),
                                      ('madeup_expense','Facilidad Administrativa'),
                                      ('salary','Salario'),
                                      ('salary_retention','Retencion de Sueldo'),
                                      ('salary_discount','Descuento de Sueldo'),
                                      ('fuel','COmbustible'),
                                      ('indirect','Indirecto'),
                                      ('negative_balance','Saldo en Contra'),
                                ], string='Tipo Linea Gasto', require=True, default='real_expense')    

    state = fields.Selection([
            ('draft', 'Borrador'),
            ('approved', 'Aprobado'),
            ('confirmed', 'Confirmado'),
            ('cancel', 'Cancelado')
            ], 'Estado Gasto',readonly=True)

    @api.model_cr
    def init(self):
        # self._table = tms_expense_analysis
        tools.drop_view_if_exists(self.env.cr, self._table)        
        # self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
        #     %s
        #     %s
        #     %s
        #     )""" % (self._table, self._select(), self._from(), self._where()))

        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
with r as 
(
select 
a.driver_helper,
a.store_id, 
a.name, 
a.date,
to_char(date_trunc('day',a.date), 'YYYY') as year,
to_char(date_trunc('day',a.date), 'MM') as month,
to_char(date_trunc('day',a.date), 'YYYY-MM-DD') as day,
a.employee_id,
a.vehicle_id, 
fv.name as vehicle_char, 
a.currency_id, 
b.product_id, 
b.name expense_line_description,
b.travel_id,
trav.route_id,
b.product_uom_qty qty,
b.price_unit,
b.price_subtotal subtotal,
b.operation_id,
b.line_type,
a.state
from tms_expense a
    inner join tms_expense_line b on a.id = b.expense_id 
    left join fleet_vehicle fv on fv.id=a.vehicle_id
    left join tms_travel trav on trav.id=b.travel_id
    where a.state <> 'cancel'

order by name, date
) select row_number() over() as id, * from r

    );""" % (self._table, ))      

    #_order = "date, store_id, name"

#     def _select(self):
#         select_str = """
#             select b.id as id,
#             a.driver_helper,
#             a.store_id, off.name store_name, a.name, 
#             a.date,
#             a.employee_id, a.vehicle_id, fv.name as vehicle_char, a.currency_id, 
#             b.product_id, --b.name expense_line_description,
#             b.product_uom_qty qty,
#             b.price_unit,
#             b.price_subtotal subtotal,
#             b.operation_id,
#             b.line_type,
#             b.travel_id,
#             trav.route_id
#         """
#         return select_str
    
#     def _from(self):
#         from_str = """    
#             from tms_expense a
#                 inner join tms_expense_line b on a.id = b.expense_id 
#                 left join fleet_vehicle fv on fv.id=a.vehicle_id
#                 inner join res_store off on off.id=a.store_id
#                 left join tms_travel trav on trav.id=b.travel_id
#         """
#         return from_str
    
#     def _where(self):
#         where_str = """
#             where a.state != 'confirmed'
#         """
#         return where_str
    
        
#     @api.model_cr
#     def init(self):
#         # self._table = tms_expense_analysis
#         tools.drop_view_if_exists(self.env.cr, self._table)        
#         self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
#             %s
#             %s
#             %s
#             )""" % (self._table, self._select(), self._from(), self._where()))        


