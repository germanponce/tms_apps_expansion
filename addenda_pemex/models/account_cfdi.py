# -*- encoding: utf-8 -*-   
from odoo import api, fields, models, _, tools
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import xml
import jinja2
from xml.parsers.expat import ExpatError


addenda_pemex ="""<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Addenda>
    <pm:Addenda_Pemex xsi:schemaLocation="http://pemex.com/facturaelectronica/addenda/v2 https://pemex.reachcore.com/schemas/addenda-pemex-v2.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:pm="http://pemex.com/facturaelectronica/addenda/v2">
        <pm:N_ACREEDOR>{{o.no_acreedor}}</pm:N_ACREEDOR>
        <pm:EJERCICIO>{{o.fiscalyear}}</pm:EJERCICIO>
        <pm:CLAVE_TRANSP>{{o.clave_transportista}}</pm:CLAVE_TRANSP>
        <pm:A_RELACION>{{o.a_relacion}}</pm:A_RELACION>
        <pm:ID_ANALITICO>{{o.id_analitico}}</pm:ID_ANALITICO>
        <pm:TIPO_PRODUCTO>T</pm:TIPO_PRODUCTO>
        <pm:CEDULA>{{o.cedula}}</pm:CEDULA>
        <pm:CONTRATO_SIIC>{{o.contrato_siic}}</pm:CONTRATO_SIIC>
        <pm:ANALITICO>{{o.analitico}}</pm:ANALITICO>
    </pm:Addenda_Pemex>
</cfdi:Addenda>"""

class ResPartner(models.Model):
    _inherit ='res.partner'

    addenda_template = fields.Selection(selection_add=[('pemex', 'Pemex')], string="Plantilla Addenda", copy=False, default='none')

    no_acreedor = fields.Char('Clave del Acreedor', size=256)
    clave_transportista = fields.Char('Clave de transportista', size=256)
    id_analitico = fields.Char('ID Analítico', size=256)
    analitico = fields.Char('Analítico', size=256)
    cedula = fields.Char('No. Cedula', size=256)
    contrato_siic = fields.Char('Contrato SIIC', size=256)


    @api.onchange('addenda_template')
    def onchange_addenda_template(self):
        if self.addenda_template and self.addenda_template == 'pemex':
            self.addenda_invoice_jinja = True
            self.addenda_invoice = addenda_pemex


class AccountInvoice(models.Model):
    _inherit ='account.invoice'

    addenda_template = fields.Selection(selection_add=[('pemex', 'Pemex')], string="Plantilla Addenda", copy=False, default='none', related="partner_id.addenda_template")
    no_acreedor = fields.Char('Clave del Acreedor', size=256, readonly=False, related="partner_id.no_acreedor")
    clave_transportista = fields.Char('Clave de transportista', size=256, readonly=False, related="partner_id.clave_transportista")
    id_analitico = fields.Char('ID Analítico', size=256, readonly=False, related="partner_id.id_analitico")
    analitico = fields.Char('Analítico', size=256, readonly=False, related="partner_id.analitico")
    cedula = fields.Char('No. Cedula', size=256, readonly=False, related="partner_id.cedula")
    contrato_siic = fields.Char('Contrato SIIC', size=256, readonly=False, related="partner_id.contrato_siic")

    fiscalyear = fields.Char('Año Relacion', size=256, readonly=False)
    a_relacion = fields.Char('Año Ejercicio', size=256, readonly=False)


    @api.onchange('addenda_template','date_invoice')
    def onchange_addenda_template(self):
        if self.addenda_template and self.addenda_template == 'pemex':
            self.addenda_invoice_jinja = True
            self.addenda_mandatory = True
            account_period = self.env['account.period']
            if self.date_invoice:
                period_invoice = account_period.find(self.date_invoice)
            else:
                period_invoice = account_period.find(self.date_invoice)
            if period_invoice:
                period_invoice = period_invoice[0]
                fiscalyear = period_invoice.fiscalyear_id.name
                self.fiscalyear = fiscalyear
                self.a_relacion = fiscalyear


    @api.onchange('addenda_mandatory')
    def onchange_addenda_mandatory_template(self):
        if self.addenda_mandatory == False:
            self.addenda_template = 'none'
    