#-*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

#PARA FECHAS
from datetime import datetime, timedelta
from pytz import timezone
import pytz
import time

from lxml import etree as et
from xml.dom import minidom
from xml.dom.minidom import parse, parseString
import base64
import re

import logging

_logger = logging.getLogger(__name__)


class SaleOrdetReportCustomDetail(models.AbstractModel):
    """Model of Customer Activity Statement"""

    _name = 'report.belchez_tms_quotation_report.quoation_report_tms'

    @api.model
    def _get_report_values(self, docids, data=None):
        context = self._context

        #valuation_data_diot
        sale_obj = self.env['sale.order']
        periods = ""
        journals = ""
        total = []
        origin_name = ""
        model = 'sale.order'
        docs = self.env[model].browse(docids)[0]
        quotation_lines = []
        account_tax  = self.env['account.tax'].sudo()
        for line in docs.order_line:
            price_reduce = line.price_unit * (1.0 - line.discount / 100.0)
            taxes = line.tax_id.compute_all(price_reduce, quantity=line.product_uom_qty, product=line.product_id, partner=docs.partner_shipping_id)['taxes']
            line_iva_16 = 0.0
            line_iva_ret_4 = 0.0
            for tax in taxes:
                tax_br = account_tax.browse(tax['id'])
                if 'IVA' in tax_br.name.upper() or tax_br.sat_code_tax == '002':
                    if tax_br.amount in (16.0,0.16):
                        line_iva_16 = tax['amount']
                if 'RET' in tax_br.name.upper():
                    if tax_br.amount in (4.0, 0.04, -4.0, -0.04):
                        line_iva_ret_4 = abs(tax['amount'])

            values = {
                'product': line.product_id,
                'line_name': line.name,
                'line_product_uom_qty': line.product_uom_qty,
                'line_product_uom': line.product_uom,
                'line_discount_amount': line.discount_amount,
                'line_price_unit': line.price_unit,
                'line_price_subtotal': line.price_subtotal,
                'line_iva_16': line_iva_16,
                'line_iva_ret_4': line_iva_ret_4,
                'line_price_total': line.price_total,
            }
            quotation_lines.append(values)
        return {
            'doc_ids': [docids[0]],
            'doc_model': model,
            'data': data,
            'docs': docs,
            'time': time,
            'quotation_lines': quotation_lines,
        }


class SaleOrder(models.Model):
    _name = 'sale.order'
    _inherit ='sale.order'


    @api.multi
    def _get_current_date(self):
        return fields.Date.context_today(self)
    
