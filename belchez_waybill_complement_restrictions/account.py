# -*- encoding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

from odoo import api, fields, models, _, tools
from datetime import datetime, date
import time
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.osv import osv, expression

import re

import logging
_logger = logging.getLogger(__name__)


# Class por Vehicles Control 
class FleetVehicle(models.Model):
    _name = 'fleet.vehicle'
    _inherit ='fleet.vehicle'

    type_stc_permit_number = fields.Char('Numero Permiso STC',
                                                     help="Atributo: NumPermisoSCT")

# Wizard que permite crear la factura de cliente de la(s) cartas porte(s) seleccionadas
class tms_waybill_invoice(models.TransientModel):
    _inherit = 'tms.waybill.invoice'

    ##### Automatizacion de los Valores para la Creacion de la Factura con datos necesarios para el Complemento #####
    def check_invoice_header_2_create(self, invoice_header, partner):
        res = super(tms_waybill_invoice, self).check_invoice_header_2_create(invoice_header=invoice_header, partner=partner)
        record_ids =  self._context.get('active_ids',[])
        waybill_obj=self.env['tms.waybill']
        waybill_br = waybill_obj.browse(record_ids[0])
        trailer_line_ids = []

        if waybill_br.vehicle_id:
            res.update({
                        'type_stc_permit_number': waybill_br.vehicle_id.type_stc_permit_number,
                       })
        return res

class AccountInvoice(models.Model):
    _inherit ='account.invoice'


    @api.onchange('vehicle_id')
    def onchange_vehicle_id_cp(self):
        if self.cfdi_complemento and self.cfdi_complemento == 'carta_porte':
            if self.vehicle_id:
                self.type_stc_permit_number = self.vehicle_id.type_stc_permit_number
                self.vehicle_plate_cp = self.vehicle_id.license_plate
                self.vehicle_year_model_cp = self.vehicle_id.model_year

    @api.constrains('invoice_line_complement_cp_ids','insurance_ids','driver_figure_ids','other_figure_ids','configuracion_federal_id', 'cfdi_complemento')
    def _check_validations_complement_waybill_on_create(self):
        _logger.info("\n########## Realizamos algunas validaciones sobre el complemento de Carta Porte >>>>>>>> ")
        context = self._context
        _logger.info("\n#### context: %s " % context)
        for rec in self:
            if 'active_model' in context and context['active_model'] == 'tms.waybill':
                return True
            if rec.cfdi_complemento == 'carta_porte':

                ######### Aseguradoras ###########
                if not rec.insurance_ids:
                    raise UserError("El complemento Carta Porte requiere de la información de la Aseguradora de Responsabilidad Civil.")
                    
                ambiental_insurance_partner_id = ""
                ambiental_insurance_policy = ""
                for insurance in rec.insurance_ids:
                    if not insurance.insurance_partner_id:
                        raise UserError("No se ha seleccionado una Aseguradora de  Responsabilidad Civil para el complemento.")
                    if not insurance.insurance_policy:
                        raise UserError("No se ha seleccionado una Póliza de Responsabilidad Civil para el complemento.")
                    ambiental_insurance_partner_id = insurance.ambiental_insurance_partner_id
                    ambiental_insurance_policy = insurance.ambiental_insurance_policy

                for line in rec.invoice_line_complement_cp_ids:
                    if line.hazardous_material == 'Sí':
                        if not ambiental_insurance_partner_id:
                            raise UserError("No se ha seleccionado una Aseguradora de Materiales Peligrosos para el complemento obligatorio si transporta Materiales Peligrosos.")
                        if not ambiental_insurance_policy:
                            raise UserError("No se ha seleccionado una Póliza de Materiales Peligrosos para el complemento obligatorio si transporta Materiales Peligrosos.")

                ######### Operadores ###########

                if not rec.driver_figure_ids:
                    raise UserError("El complemento Carta Porte requiere la información de los Operadores.")

                for driver in rec.driver_figure_ids:
                    if not driver.partner_id:
                        raise UserError("No se ha seleccionado una dirección para el Operador.")
                    driver_cp_vat = driver.driver_cp_vat
                    if not driver_cp_vat:
                        raise UserError("El Operador (%s) no cuenta con un RFC." % driver.partner_id.name)
                    
                    if len(driver_cp_vat) == 12:
                        _logger.info("\n#-- RFC de Personas Morales -->")
                        re_rfc = '^(([A-Z]|[a-z]){3})([0-9]{6})((([A-Z]|[a-z]|[0-9]){3}))'
                        _check_rfc = re.compile(re_rfc)
                        if not _check_rfc.match(driver_cp_vat):
                            _logger.info("\n:::: El RFC no tiene una estructura valida :::> ")
                            raise UserError("El Operador (%s) no cuenta con un RFC (%s) con estructura valida." % (driver.partner_id.name, driver_cp_vat))
                        else:
                            _logger.info("\n:::: El RFC tiene una estructura valida :::> ")
                    else:
                        _logger.info("\n#-- RFC de Personas Fisicas -->")
                        re_rfc = '^(([A-Z]|[a-z]|\s){1})(([A-Z]|[a-z]){3})([0-9]{6})((([A-Z]|[a-z]|[0-9]){3}))'
                        _check_rfc = re.compile(re_rfc)
                        if not _check_rfc.match(driver_cp_vat):
                            _logger.info("\n:::: El RFC no tiene una estructura valida :::> ")
                            raise UserError("El Operador (%s) no cuenta con un RFC (%s) con estructura valida." % (driver.partner_id.name, driver_cp_vat))
                        else:
                            _logger.info("\n:::: El RFC tiene una estructura valida :::> ")

                    cp_driver_license = driver.cp_driver_license
                    if not cp_driver_license:
                        raise UserError("El Operador (%s) tiene ingresado el No. de Licencia." % driver.partner_id.name)
                
                ######### Remolques ###########
                if rec.configuracion_federal_id.code in ('C3','T3S3S2'):
                    if not rec.trailer_line_ids:
                        raise UserError("Los Remolques/Semiremolques son obligatorios para la configuración C3 y T3S3S2.")
                    for trailer in rec.trailer_line_ids:
                        if not trailer.subtype_trailer_id:
                            raise UserError("No se ingreso la información Subtipo Remolque para el complemento.")
                        if not trailer.trailer_plate_cp:
                            raise UserError("No se ingreso la información Placa de Remolque para el complemento.")

                if rec.tipo_transporte_id and rec.tipo_transporte_id.code == '01':
                    ### Validación ####
                    ### Validando que tenga Mercancias Transportadas ###
                    if not rec.invoice_line_complement_cp_ids:
                        raise UserError("Para el complemento de Carta Porte es necesario indicar las Mercancias Transportadas.")
                    else:
                        #### Validando el nodo de Dimensiones y atributos de Mercancias ###
                        for merchandise in rec.invoice_line_complement_cp_ids:
                            if merchandise.quantity <= 0.0:
                                raise UserError("La cantidad transportada para el producto %s debe ser mayor a 0.0" % merchandise.description)

                            if merchandise.weight_charge <= 0.0:
                                raise UserError("El peso para el producto %s debe ser mayor a 0.0" % merchandise.description)
                            
                            dimensions_charge = merchandise.dimensions_charge
                            if dimensions_charge and dimensions_charge != '0/0/0plg':
                                _merchandise_re = re.compile('[0-9]{2}[/]{1}[0-9]{2}[/]{1}[0-9]{2}cm|[0-9]{2}[/]{1}[0-9]{2}[/]{1}[0-9]{2}plg')
                                if not _merchandise_re.match(dimensions_charge):
                                    raise UserError(_('Verifique su información\n\nLas dimensiones establecidas "%s" \
                                         no se apega a los lineamientos del SAT.\nEjemplo: 30/20/10plg\nExpresión Regular: [0-9]{2}[/]{1}[0-9]{2}[/]{1}[0-9]{2}cm|[0-9]{2}[/]{1}[0-9]{2}[/]{1}[0-9]{2}plg') % (dimensions_charge))
                            if merchandise.quantity == 0.0:
                                raise UserError("La cantidad a transportar debe ser diferente de 0.0.\nProducto:%s" % merchandise.description)

                    ### Si el CFDI es de Tipo Ingreso debe tener información de retenciones y traslados ####
                    if rec.type_document_id.code == 'I' and rec.amount_total > 0.0:
                        tax_ret = False
                        tax_trasl = False
                        for taxline in rec.tax_line_ids:
                            if taxline.tax_percent < 0.0:
                                tax_ret = True
                            elif taxline.tax_percent > 0.0:
                                tax_trasl = True
                        
                        customer_country_code = rec.partner_id.country_id.code if rec.partner_id.country_id else ""

                        if not tax_ret:
                            if customer_country_code == 'MX':
                                raise UserError("Cuando se utiliza el complemento de Carta Porte para Transporte Federal \
                                                 en un comprobante de tipo Ingreso (I), \
                                                 el nodo de Impuestos Retenidos no puede estar vacio.")
                        if not tax_trasl:
                            if customer_country_code == 'MX':
                                raise UserError("Cuando se utiliza el complemento de Carta Porte para Transporte Federal \
                                                 en un comprobante de tipo Ingreso (I), \
                                                 el nodo de Impuestos Trasladados no puede estar vacio.")
    
    def _check_validations_complement_waybill(self):
        _logger.info("\n########## ext _check_validations_complement_waybill >>>>>>>> ")
        res = super(AccountInvoice, self)._check_validations_complement_waybill()
        context = self._context
        _logger.info("\n#### context: %s " % context)
        for rec in self:
            if rec.cfdi_complemento == 'carta_porte':
                ######### Aseguradoras ###########
                if not rec.insurance_ids:
                    raise UserError("El complemento Carta Porte requiere de la información de la Aseguradora de Responsabilidad Civil.")
                    
                ambiental_insurance_partner_id = ""
                ambiental_insurance_policy = ""
                for insurance in rec.insurance_ids:
                    if not insurance.insurance_partner_id:
                        raise UserError("No se ha seleccionado una Aseguradora de  Responsabilidad Civil para el complemento.")
                    if not insurance.insurance_policy:
                        raise UserError("No se ha seleccionado una Póliza de Responsabilidad Civil para el complemento.")
                    ambiental_insurance_partner_id = insurance.ambiental_insurance_partner_id
                    ambiental_insurance_policy = insurance.ambiental_insurance_policy

                for line in rec.invoice_line_complement_cp_ids:
                    if line.hazardous_material == 'Sí':
                        if not ambiental_insurance_partner_id:
                            raise UserError("No se ha seleccionado una Aseguradora de Materiales Peligrosos para el complemento obligatorio si transporta Materiales Peligrosos.")
                        if not ambiental_insurance_policy:
                            raise UserError("No se ha seleccionado una Póliza de Materiales Peligrosos para el complemento obligatorio si transporta Materiales Peligrosos.")

                ######### Operadores ###########

                if not rec.driver_figure_ids:
                    raise UserError("El complemento Carta Porte requiere la información de los Operadores.")

                for driver in rec.driver_figure_ids:
                    if not driver.partner_id:
                        raise UserError("No se ha seleccionado una dirección para el Operador.")
                    driver_cp_vat = driver.driver_cp_vat
                    if not driver_cp_vat:
                        raise UserError("El Operador (%s) no cuenta con un RFC." % driver.partner_id.name)
                    
                    if len(driver_cp_vat) == 12:
                        _logger.info("\n#-- RFC de Personas Morales -->")
                        re_rfc = '^(([A-Z]|[a-z]){3})([0-9]{6})((([A-Z]|[a-z]|[0-9]){3}))'
                        _check_rfc = re.compile(re_rfc)
                        if not _check_rfc.match(driver_cp_vat):
                            _logger.info("\n:::: El RFC no tiene una estructura valida :::> ")
                            raise UserError("El Operador (%s) no cuenta con un RFC (%s) con estructura valida." % (driver.partner_id.name, driver_cp_vat))
                        else:
                            _logger.info("\n:::: El RFC tiene una estructura valida :::> ")
                    else:
                        _logger.info("\n#-- RFC de Personas Fisicas -->")
                        re_rfc = '^(([A-Z]|[a-z]|\s){1})(([A-Z]|[a-z]){3})([0-9]{6})((([A-Z]|[a-z]|[0-9]){3}))'
                        _check_rfc = re.compile(re_rfc)
                        if not _check_rfc.match(driver_cp_vat):
                            _logger.info("\n:::: El RFC no tiene una estructura valida :::> ")
                            raise UserError("El Operador (%s) no cuenta con un RFC (%s) con estructura valida." % (driver.partner_id.name, driver_cp_vat))
                        else:
                            _logger.info("\n:::: El RFC tiene una estructura valida :::> ")

                    cp_driver_license = driver.cp_driver_license
                    if not cp_driver_license:
                        raise UserError("El Operador (%s) tiene ingresado el No. de Licencia." % driver.partner_id.name)
                
                ######### Remolques ###########
                if rec.configuracion_federal_id.code in ('C3','T3S3S2'):
                    if not rec.trailer_line_ids:
                        raise UserError("Los Remolques/Semiremolques son obligatorios para la configuración C3 y T3S3S2.")
                    for trailer in rec.trailer_line_ids:
                        if not trailer.subtype_trailer_id:
                            raise UserError("No se ingreso la información Subtipo Remolque para el complemento.")
                        if not trailer.trailer_plate_cp:
                            raise UserError("No se ingreso la información Placa de Remolque para el complemento.")

                if rec.tipo_transporte_id and rec.tipo_transporte_id.code == '01':
                    ### Validación ####
                    ### Validando que tenga Mercancias Transportadas ###
                    if not rec.invoice_line_complement_cp_ids:
                        raise UserError("Para el complemento de Carta Porte es necesario indicar las Mercancias Transportadas.")
                    else:
                        #### Validando el nodo de Dimensiones y atributos de Mercancias ###
                        for merchandise in rec.invoice_line_complement_cp_ids:
                            if merchandise.quantity <= 0.0:
                                raise UserError("La cantidad transportada para el producto %s debe ser mayor a 0.0" % merchandise.description)

                            if merchandise.weight_charge <= 0.0:
                                raise UserError("El peso para el producto %s debe ser mayor a 0.0" % merchandise.description)
                            
        return res

class InvoiceLineComplementCP(models.Model):
    _inherit = 'invoice.line.complement.cp'

    validity_quantity_weight = fields.Boolean('Validar cantidad y peso')

    default_dimensions_uom = fields.Char('UdM dimensiones', size=16, default="plg")

    dimensions_charge2 = fields.Char('Dimensiones', size=128)


    @api.model
    def create(self, vals):
        dimensions_charge2 = vals.get('dimensions_charge2', False)
        dimensions_charge = vals.get('dimensions_charge', False)
        if dimensions_charge2:
            if 'PLG' in dimensions_charge2:
                dimensions_charge2 = dimensions_charge2.replace('PLG', '')
                vals.update({'dimensions_charge2': dimensions_charge2})
                vals.update({'dimensions_charge': dimensions_charge2+"plg"})
            if 'plg' in dimensions_charge2:
                dimensions_charge2 = dimensions_charge2.replace('plg', '')
                vals.update({'dimensions_charge2': dimensions_charge2})
                vals.update({'dimensions_charge': dimensions_charge2+"plg"})
            if 'CM' in dimensions_charge2:
                dimensions_charge2 = dimensions_charge2.replace('CM', '')
                vals.update({'dimensions_charge2': dimensions_charge2})
                vals.update({'dimensions_charge': dimensions_charge2+"plg"})
            if 'cm' in dimensions_charge2:
                dimensions_charge2 = dimensions_charge2.replace('cm', '')
                vals.update({'dimensions_charge2': dimensions_charge2})
                vals.update({'dimensions_charge': dimensions_charge2+"plg"})
        if dimensions_charge and not dimensions_charge2:
            if 'PLG' in dimensions_charge:
                dimensions_charge = dimensions_charge.replace('PLG', '')
                vals.update({'dimensions_charge2': dimensions_charge})
            if 'plg' in dimensions_charge:
                dimensions_charge = dimensions_charge.replace('plg', '')
                vals.update({'dimensions_charge2': dimensions_charge})
            if 'CM' in dimensions_charge:
                dimensions_charge = dimensions_charge.replace('CM', '')
                vals.update({'dimensions_charge2': dimensions_charge})
            if 'cm' in dimensions_charge:
                dimensions_charge = dimensions_charge.replace('cm', '')
                vals.update({'dimensions_charge2': dimensions_charge})
        res = super(InvoiceLineComplementCP, self).create(vals)

        return res

    @api.onchange('dimensions_charge2')
    def onchange_dimensions_charge2(self):
        dimensions_charge2 = ""
        if self.dimensions_charge2:
            dimensions_charge2 = self.dimensions_charge2
            if 'PLG' in self.dimensions_charge2:
                dimensions_charge2 = self.dimensions_charge2.replace('PLG', '')
                self.dimensions_charge2 = dimensions_charge2
            if 'plg' in self.dimensions_charge2:
                dimensions_charge2 = self.dimensions_charge2.replace('plg', '')
                self.dimensions_charge2 = dimensions_charge2
            if 'CM' in self.dimensions_charge2:
                dimensions_charge2 = self.dimensions_charge2.replace('CM', '')
                self.dimensions_charge2 = dimensions_charge2
            if 'cm' in self.dimensions_charge2:
                dimensions_charge2 = self.dimensions_charge2.replace('cm', '')
                self.dimensions_charge2 = dimensions_charge2
        if dimensions_charge2:
            self.dimensions_charge = dimensions_charge2+"plg"

    @api.onchange('quantity','weight_charge','description')
    def onchange_transport_merchandise(self):
        if self.validity_quantity_weight:
            if self.quantity <= 0.0:
                # raise UserError("La cantidad transportada para el producto %s debe ser mayor a 0.0" % self.description)
                warning_mess = {
                    'title': 'Complemento Carta Porte!',
                    'message' : 'La cantidad transportada para el producto %s debe ser mayor a 0.0' % self.description,
                }
                return {'warning': warning_mess}

            if self.weight_charge <= 0.0:
                # raise UserError("El peso para el producto %s debe ser mayor a 0.0" % self.description)
                warning_mess = {
                        'title': 'Complemento Carta Porte!',
                        'message' : 'El peso para el producto %s debe ser mayor a 0.0'  % self.description,
                }
                return {'warning': warning_mess}
        else:
            if self.quantity > 0.0 or self.weight_charge > 0.0:
                self.validity_quantity_weight = True


    @api.constrains('quantity','weight_charge','description')
    def _check_validations_transport_merchandise(self):
        for rec in self:
            if rec.quantity <= 0.0:
                raise UserError("La cantidad transportada para el producto %s debe ser mayor a 0.0" % rec.description)

            if rec.weight_charge <= 0.0:
                raise UserError("El peso para el producto %s debe ser mayor a 0.0" % rec.description)
