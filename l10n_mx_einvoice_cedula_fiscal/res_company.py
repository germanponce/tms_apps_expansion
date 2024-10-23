# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to OpenERP, Open Source Management Solution
#
############################################################################
#    Coded by: German Ponce Dominguez (german.ponce@outlook.com)
############################################################################

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

import base64

from pytz import timezone
import pytz
from datetime import timedelta



class ResCompany(models.Model):
    _name = 'res.company'
    _inherit ='res.company'

    cedula_png = fields.Binary('Cedula Fiscal')


class AccountInvoice(models.Model):
    _name = 'account.invoice'
    _inherit ='account.invoice'

    @api.multi
    def get_colonia_fromzip_report(self, zip_sat_id, colonia_sat_id):
        try:
            invoice = self[0]
        except:
            invoice = self
        if colonia_sat_id:
            return "Col. "+colonia_sat_id.name
        if zip_sat_id:
            colonia_sat_id = self.env['res.colonia.zip.sat.code'].sudo().search([('zip_sat_code','=',zip_sat_id.id)])
            if colonia_sat_id:
                colonia_sat_id = colonia_sat_id[0]
                return "Col. "+colonia_sat_id.name
            else:
                return "Col. "
        else:
            if invoice.partner_id.street2:
                return "Col. "+invoice.street2