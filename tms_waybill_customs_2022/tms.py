# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _name = 'res.company'
    _inherit ='res.company'

    restrict_multi_partners_on_waybill = fields.Boolean(string="Restringir un viaje para cliente exclusivo", help='Restringe que se puedan mezclar viajes de diferentes clientes en una sola carta porte.')

    restrict_multi_number_top_waybill = fields.Boolean(string="Restringir número de Cartas Porte por viaje", help='Restringe el no. de cartas porte maximo.')
    
    restrict_multi_number_top_waybill_number = fields.Integer(string="Número Maximo", help='Restringe el no. de cartas porte maximo.')

    restrict_waybill_number_from_framework = fields.Boolean(string="Validar Cartas Porte Viajes segun armado", help='Restringe el no. de cartas porte segun el armado.\n* Sencillo 1 Carta Porte\n* Full 2 Cartas Porte.')


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    restrict_multi_partners_on_waybill = fields.Boolean(string="Restringir un viaje para cliente exclusivo", related='company_id.restrict_multi_partners_on_waybill', readonly=False, help='Restringe que se puedan mezclar viajes de diferentes clientes en una sola carta porte.', )

    restrict_multi_number_top_waybill = fields.Boolean(string="Restringir número de Cartas Porte por viaje", related='company_id.restrict_multi_number_top_waybill', readonly=False, help='Restringe el no. de cartas porte maximo.', )

    restrict_multi_number_top_waybill_number = fields.Integer(string="Número Maximo", related='company_id.restrict_multi_number_top_waybill_number', readonly=False, help='Restringe el no. de cartas porte maximo.', )
    
    restrict_waybill_number_from_framework = fields.Boolean(string="Validar Cartas Porte Viajes segun armado", related='company_id.restrict_waybill_number_from_framework', readonly=False, help='Restringe el no. de cartas porte segun el armado.\n* Sencillo 1 Carta Porte\n* Full 2 Cartas Porte.')


class TmsTravel(models.Model):
    _inherit ='tms.travel'

    @api.multi    
    def action_dispatch(self):
        for rec in self:
            if rec.company_id.restrict_waybill_number_from_framework:
                if rec.framework == 'Double':
                    framework_count = 2
                    if rec.waybill_ids:
                        waybills_count = len(rec.waybill_ids)
                        if waybills_count != 2:
                            raise UserError("No coincide numero de Cartas Porte con el tipo de viaje full.\n")
                elif rec.framework == 'Single':
                    framework_count = 1
                    if rec.waybill_ids:
                        waybills_count = len(rec.waybill_ids)
                        if waybills_count != 1:
                            raise UserError("No coincide numero de Cartas Porte con el tipo de viaje senillo.\n")
                else:
                    #rec.framework = 'Unit'
                    framework_count = 0

        res = super(TmsTravel, self).action_dispatch()
        return res

    @api.constrains('waybill_ids')
    def _constraint_waybill_ids(self):
        for rec in self:
            if rec.company_id.restrict_multi_partners_on_waybill:
                partner_id = False
                partner_name = False
                i = 1
                partner_list_ids = []
                last_waybill_name = ""
                for waybill in rec.waybill_ids:
                    _logger.info("\n### Carta Porte #: %s" % i)
                    partner_id = waybill.partner_id.id
                    if not partner_name:
                        partner_name = waybill.partner_id.name
                    if waybill.partner_id.parent_id:
                        partner_id = waybill.partner_id.parent_id.id
                    if partner_id not in partner_list_ids:
                        partner_list_ids.append(waybill.partner_id.id)
                    last_waybill_name = waybill.name
                    # if not partner_id:
                    #     partner_id = waybill.partner_id.id
                    #     partner_name = waybill.partner_id.name
                    #     if waybill.partner_id.parent_id:
                    #         partner_id = waybill.partner_id.parent_id.id
                    #         partner_name = waybill.partner_id.parent_id.name
                    # else:
                    #     if partner_id != waybill.partner_id.id:
                    #         if waybill.partner_id.parent_id:
                    #             if partner_id != waybill.partner_id.parent_id.id:
                    #                 raise UserError("No se puede esar esta Carta Porte %s.\nEl viaje ya tiene una Carta Porte previa relacionada con el cliente %s." % (waybill.name, partner_name))
                    #         else:
                    #             raise UserError("No se puede esar esta Carta Porte %s.\nEl viaje ya tiene una Carta Porte previa relacionada con el cliente %s." % (waybill.name, partner_name))
                    i += 1
                if len(partner_list_ids) > 1:
                    raise UserError("No se puede esar esta Carta Porte %s.\nEl viaje ya tiene una Carta Porte previa relacionada con el cliente %s." % (last_waybill_name, partner_name))
            if rec.company_id.restrict_multi_partners_on_waybill:
                if rec.waybill_ids:
                    waybills_count = len(rec.waybill_ids)
                    if rec.company_id.restrict_multi_number_top_waybill_number > 0:
                        if waybills_count > rec.company_id.restrict_multi_number_top_waybill_number:
                            raise UserError("No se puede usar esta Carta Porte %s.\nEl viaje ha rebasado el número de Cartas Porte relacionadas permitidas, el cual es de %s." % (waybill.name, rec.company_id.restrict_multi_number_top_waybill_number))


class TmsWaybill(models.Model):
    _inherit ='tms.waybill'


    upload_point     = fields.Char(string='Upload Point', size=512, readonly=False, states={'confirmed': [('readonly', True)]})
    download_point   = fields.Char(string='Download Point', size=512, required=False, readonly=False, 
                                   states={'confirmed': [('readonly', True)]})

    x_reference = fields.Char('Referencia', size=256, copy=False)

    x_eco_bel = fields.Char('ECO Prog Ref.', size=128)

    x_eco_bel_id = fields.Many2one('fleet.vehicle', 'ECO Prog')

    x_operador_bel = fields.Char('Operador Prog Ref.', size=128)

    x_operador_bel_id = fields.Many2one('hr.employee', 'Operador Prog')

    number_waybills_count = fields.Integer('No. Cartas Porte Asociadas a los Viajes')


    x_eco_retiro = fields.Char('Eco Retiro', size=128)

    x_eco_retiro_id = fields.Many2one('fleet.vehicle','Eco Retiro')

    x_operador_retiro = fields.Char('Operador Retiro', size=128)

    x_operador_retiro_id = fields.Many2one('hr.employee', 'Operador Retiro')

    x_mov_ingreso_bel = fields.Char('Operador Ingreso', size=128)

    x_mov_ingreso_bel_id = fields.Many2one('hr.employee', 'Operador Ingreso')

    x_eco_ingreso = fields.Char('Eco Ingreso', size=128)

    x_eco_ingreso_id = fields.Many2one('fleet.vehicle','Eco Ingreso')

    @api.onchange('x_eco_bel_id')
    def onchange_x_eco_bel_id(self):
        if self.x_eco_bel_id:
            self.x_eco_bel = self.x_eco_bel_id.name
        else:
            if self.x_eco_bel:
                self.x_eco_bel = False

    @api.onchange('x_eco_ingreso_id')
    def onchange_x_eco_ingreso_id(self):
        if self.x_eco_ingreso_id:
            self.x_eco_ingreso = self.x_eco_ingreso_id.name
        else:
            if self.x_eco_ingreso:
                self.x_eco_ingreso = False

    @api.onchange('x_mov_ingreso_bel_id')
    def onchange_x_mov_ingreso_bel_id(self):
        if self.x_mov_ingreso_bel_id:
            self.x_mov_ingreso_bel = self.x_mov_ingreso_bel_id.name
        else:
            if self.x_mov_ingreso_bel:
                self.x_mov_ingreso_bel = False

    @api.onchange('x_operador_retiro_id')
    def onchange_x_operador_retiro_id(self):
        if self.x_operador_retiro_id:
            self.x_operador_retiro = self.x_operador_retiro_id.name
        else:
            if self.x_operador_retiro:
                self.x_operador_retiro = False

    @api.onchange('x_eco_retiro_id')
    def onchange_x_eco_retiro_id(self):
        if self.x_eco_retiro_id:
            self.x_eco_retiro = self.x_eco_retiro_id.name
        else:
            if self.x_eco_retiro:
                self.x_eco_retiro = False

    @api.onchange('x_operador_bel_id')
    def onchange_x_operador_bel_id(self):
        if self.x_operador_bel_id:
            self.x_operador_bel = self.x_operador_bel_id.name
        else:
            if self.x_operador_bel:
                self.x_operador_bel = False

    @api.onchange('travel_ids')
    def onchange_number_waybills_count(self):
        number_waybills_count = 0
        if self.travel_ids:
            for travel in self.travel_ids:
                if travel.waybill_ids:
                    waybills_count = len(travel.waybill_ids)
                    number_waybills_count += waybills_count
            self.number_waybills_count = number_waybills_count

    @api.constrains('travel_ids')
    def _constraint_travel_ids(self):
        for rec in self:
            if rec.company_id.restrict_multi_partners_on_waybill:
                partner_id = False
                partner_name = False
                for travel in rec.travel_ids:
                    for waybill in  travel.waybill_ids:
                        if waybill.id != rec.id:
                            partner_id = waybill.partner_id.id
                            partner_name = waybill.partner_id.name
                            if waybill.partner_id.parent_id:
                                partner_id = waybill.partner_id.parent_id.id
                                partner_name = waybill.partner_id.parent_id.name

                            if partner_id != rec.partner_id.id:
                                if rec.partner_id.parent_id:
                                    if partner_id != rec.partner_id.parent_id:
                                        raise UserError("No se puede esar este viaje %s.\nEl viaje ya tiene una carta porte relacionada con el cliente %s." % (travel.name, partner_name))
                                else:
                                    raise UserError("No se puede esar este viaje %s.\nEl viaje ya tiene una carta porte relacionada con el cliente %s." % (travel.name, partner_name))
                    
                    if rec.company_id.restrict_multi_partners_on_waybill:
                        if travel.waybill_ids:
                            waybills_count = len(travel.waybill_ids)
                            if rec.company_id.restrict_multi_number_top_waybill_number > 0:
                                if waybills_count > rec.company_id.restrict_multi_number_top_waybill_number:
                                    raise UserError("No se puede usar este viaje %s.\nEl viaje ha rebasado el número de cartas porte relacionadas  permitidas, el cual es de %s." % (travel.name, rec.company_id.restrict_multi_number_top_waybill_number))

    @api.multi
    def action_confirm(self):
        for rec in self:
            if not rec.x_reference:
                raise UserError('El campo "Referencia" se encuentra vacio. Falta referencia de contenedor.')
        res = super(TmsWaybill, self).action_confirm()
        return res

    @api.onchange('x_reference')
    def onchange_x_reference(self):
        if self.waybill_shipped_product and self.x_reference:
            for wshipped in self.waybill_shipped_product:
                wshipped.notes = self.x_reference
    

class TmsWaybillLine(models.Model):
    _inherit ='tms.waybill.line'

    notes = fields.Text('Notas', copy=False)


class WaybillTravelWizard(models.TransientModel):
    _inherit ='tms.waybill.travel.wizard'

    # def _get_waybill_info_vehicle(self):
    #     print ("######## _get_waybill_info_vehicle >>>>>>>>>")
    #     vehicle_id = False
    #     active_model = self._context.get('active_model')
    #     active_ids = self._context.get('active_ids')
    #     # Checks on context parameters
    #     print ("######## active_model: ",active_model)
    #     print ("######## active_ids: ",active_ids)
    #     if active_model and active_ids:
    #         # Checks on received invoice records
    #         waybill = self.env[active_model].browse(active_ids)
    #         print ("######## waybill.x_eco_bel_id: ",waybill.x_eco_bel_id)

    #         if waybill.x_eco_bel_id:
    #             vehicle_id = waybill.x_eco_bel_id.id
    #     print ("### vehicle_id: ", vehicle_id)
    #     return vehicle_id

    # def _get_waybill_info_driver(self):
    #     print ("######## _get_waybill_info_driver >>>>>>>>>")
    #     employee_id = False
    #     active_model = self._context.get('active_model')
    #     active_ids = self._context.get('active_ids')
    #     # Checks on context parameters
    #     print ("######## active_model: ",active_model)
    #     print ("######## active_ids: ",active_ids)
    #     if active_model and active_ids:
    #         # Checks on received invoice records
    #         waybill = self.env[active_model].browse(active_ids)
    #         print ("######## waybill.x_eco_bel_id: ",waybill.x_eco_bel_id)
    #         print ("######## waybill.x_operador_bel_id: ",waybill.x_operador_bel_id)

    #         if waybill.x_operador_bel_id:
    #             employee_id = waybill.x_operador_bel_id.id
    #     print ("### employee_id: ", employee_id)
    #     return employee_id

    # vehicle_id         = fields.Many2one('fleet.vehicle', string='Vehiculo Transportista', required=True, default=_get_waybill_info_vehicle)

    # employee_id     = fields.Many2one('hr.employee', string='Operador', required=True, default=_get_waybill_info_driver)


    @api.onchange('vehicle_id')
    def onchange_vehicle_id(self):
        if self.vehicle_id:
            self.supplier_id = self.vehicle_id.supplier_id.id
            if not self.employee_id:
                self.employee_id = self.vehicle_id.employee_id.id

        
    @api.onchange('kit_id')
    def onchange_kit_id(self):
        if self.kit_id:
            self.vehicle_id = self.kit_id.vehicle_id.id
            self.trailer1_id = self.kit_id.trailer1_id.id
            self.trailer2_id = self.kit_id.trailer2_id.id
            self.dolly_id = self.kit_id.dolly_id.id
            self.employee_id = self.kit_id.employee_id.id


    @api.model
    def default_get(self, fields):
        rec = super(WaybillTravelWizard, self).default_get(fields)
        active_model = self._context.get('active_model')
        active_ids = self._context.get('active_ids')
        # Checks on context parameters
        if active_model and active_ids:
            # Checks on received invoice records
            waybill = self.env[active_model].browse(active_ids)

            if waybill.operation_id:
                rec.update({'operation_id': waybill.operation_id.id})
            if waybill.x_eco_bel_id:
                rec.update({'vehicle_id': waybill.x_eco_bel_id.id})
            if waybill.x_operador_bel_id:
                rec.update({'employee_id': waybill.x_operador_bel_id.id})
        return rec