# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################

import time
import math

from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, exceptions, fields, models, _
from pytz import timezone
import odoo.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)



class TmsWaybillShippedProduct(models.Model):
    _name = 'tms.waybill.shipped_product'
    _inherit ='tms.waybill.shipped_product'


    need_compute_volume = fields.Boolean('T. Calculada Vol.')

    product_volume_upload = fields.Float('Volumen Carga', digits=(14,6), help='Volumen de Carga', )

    product_volume_download = fields.Float('Volumen Descarga', digits=(14,6), help='Volumen de descarga', )

    product_temperature_upload = fields.Float('Temperatura Carga', digits=(14,6), help='Temperatura de carga', )

    product_temperature_download = fields.Float('Temperatura Descarga', digits=(14,6), help='Temperatura de descarga', )

    ### Campo Basado en las Tarifas ###
    # @api.onchange('waybill_id','waybill_id.waybill_customer_factor')
    # def onchange_product_uom_need_vol(self):
    #     if self.waybill_id and self.waybill_id.waybill_customer_factor:
    #         need_compute_volume = False
    #         for xline in self.waybill_id.waybill_customer_factor:
    #             if xline.factor_type == 'volume':
    #                 need_compute_volume = True
    #                 break
    #         self.need_compute_volume = need_compute_volume

    ### Campo Basado en las UdM ###
    @api.onchange('product_uom')
    def onchange_product_uom_need_vol(self):
        need_compute_volume = False
        if self.product_uom and self.product_uom.category_id.with_context({'lang':'en_US'}).name.upper() in ('VOLUME','VOLUMEN'):
            need_compute_volume = True
        self.need_compute_volume = need_compute_volume


    @api.onchange('product_id')
    def on_change_product_id(self):
        res = super(TmsWaybillShippedProduct, self).on_change_product_id()
        ### Campo Basado en las Tarifas ###
        # if self.waybill_id and self.waybill_id.waybill_customer_factor:
        #     need_compute_volume = False
        #     for xline in self.waybill_id.waybill_customer_factor:
        #         if xline.factor_type == 'volume':
        #             need_compute_volume = True
        #             break
        #     self.need_compute_volume = need_compute_volume
        ### Campo Basado en las UdM ###
        need_compute_volume = False
        if self.product_uom and self.product_uom.category_id.with_context({'lang':'en_US'}).name.upper() in ('VOLUME','VOLUMEN'):
            need_compute_volume = True
        self.need_compute_volume = need_compute_volume
        return res


class TmsWaybill(models.Model):
    _name = 'tms.waybill'
    _inherit ='tms.waybill'

    @api.multi
    @api.depends('waybill_shipped_product','waybill_customer_factor')
    def _check_need_compute_volume(self):
        for rec in self:
            need_compute_volume = False
            for xline in rec.waybill_customer_factor:
                if xline.factor_type == 'volume':
                    need_compute_volume = True
                    break
            rec.need_compute_volume = need_compute_volume

    @api.multi
    @api.depends('waybill_shipped_product')
    def _shipped_product(self):
        for wb in self:
            volume, weight, qty = 0.0, 0.0, 0.0
            for shipped_prod in wb.waybill_shipped_product:
                if shipped_prod.product_uom.category_id.with_context({'lang':'en_US'}).name.upper() not in ('VOLUME','VOLUMEN') and shipped_prod.product_volume_upload:
                    raise UserError("Ocurrio un Error durante el calculo de la información.\nLa Categoria de la Unidad de Medida del Producto Transportado %s no corresponde a Unidades de Volumen y se tiene ingresado un valor para Volumen de Carga.\nLa Categoria debe ser Volumen o no debe existir un valor dentro de la Columna Volumen de Carga." % (shipped_prod.name, ))
                if shipped_prod.product_uom.category_id.with_context({'lang':'en_US'}).name.upper() in ('VOLUME','VOLUMEN'):
                    volume += shipped_prod.product_volume_upload
                elif shipped_prod.product_uom.category_id.with_context({'lang':'en_US'}).name.upper() in ('WEIGHT','PESO'):
                    weight += shipped_prod.weight_real or shipped_prod.weight_estimation
                else:
                    qty += shipped_prod.product_uom_qty
            wb.product_qty       = qty
            wb.product_volume    = volume
            wb.product_weight    = weight
            try:
                wb.product_uom_type  = shipped_prod.product_uom.category_id.name
            except:
                wb.product_uom_type  = False

    need_compute_volume = fields.Boolean('T. Calculada Vol.', compute="_check_need_compute_volume", store=True)




# class TmsFactor(models.Model):
#     _name = 'tms.factor'
#     _inherit ='tms.factor'


    # def calculate(self, record_type, waybill, calc_type=None, travel_ids=False, driver_helper=False):
    #     result = 0.0
    #     print ("#### record_type >>>>>>>>> ",record_type)
    #     print ("#### waybill >>>>>>>>> ", waybill.need_compute_volume)
    #     print ("#### waybill >>>>>>>>> ", waybill)
    #     print ("#### calc_type >>>>>>>>> ")
    #     if record_type == 'waybill' and waybill.need_compute_volume == True:
    #         for factor in (waybill.waybill_customer_factor if calc_type=='client' else waybill.expense_driver_factor if calc_type=='driver' else waybill.waybill_supplier_factor):
    #             if factor.factor_type in ('distance', 'distance_real') and \
    #                 (factor.framework=='Any' or factor.framework == waybill.travel_id.framework) and\
    #                 (factor.vehicle_type_id and factor.vehicle_type_id==waybill.travel_id.vehicle_id.vehicle_type_id or True):                
    #                 if not waybill.travel_id.id:
    #                     raise ValidationError(_('Warning !!!\nCould calculate Freight Amount !  Waybill %s is not assigned to a Travel') % (waybill.name))
    #                 x = (float(waybill.travel_id.route_id.distance) if factor.factor_type=='distance' else float(waybill.travel_id.distance_extraction)) if factor.framework == 'Any' or factor.framework == waybill.travel_id.framework else 0.0

    #             elif factor.factor_type == 'weight':
    #                 if not waybill.product_weight:
    #                     raise ValidationError(_('Warning !!!\nCould calculate Freight Amount ! Waybill %s has no Products with UoM Category = Weight or Product Qty = 0.0' % waybill.name))
    #                 x = float(waybill.product_weight)

    #             elif factor.factor_type == 'qty':
    #                 if not waybill.product_qty:
    #                     raise ValidationError(_('Warning !!!\nCould calculate Freight Amount ! Waybill %s has no Products with Quantity > 0.0') % (waybill.name))
    #                 x = float(waybill.product_qty)

    #             elif factor.factor_type == 'volume':
    #                 if not waybill.product_volume:
    #                     raise ValidationError(_('Aviso !!!\nNo se pudo calcular el monto de Flete ! La Carta Porte %s no tiene valores dentro del campo Volumen de Carga; el Factor indica que debe ser calculado en base al Volumen del Producto') % (waybill.name))
    #                 x = float(waybill.product_volume)

    #             elif factor.factor_type == 'percent':
    #                 x = float(waybill.amount_freight) / 100.0

    #             elif factor.factor_type == 'travel':
    #                 x = 0.0

    #             elif factor.factor_type == 'special':
    #                 exec(factor.factor_special_id.python_code)


    #             result += ((factor.fixed_amount if (factor.mixed or factor.factor_type=='travel') else 0.0)+ (factor.factor * x if factor.factor_type != 'special' else x)) if (((x >= factor.range_start and x <= factor.range_end) or (factor.range_start == factor.range_end == 0.0)) and factor.driver_helper==driver_helper) else 0.0

    #     else:
    #         res_spr = super(TmsFactor, self).calculate(record_type, waybill, calc_type, travel_ids, driver_helper)
    #         return res_spr
    #     return result
    