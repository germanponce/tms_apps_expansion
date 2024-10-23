# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 German Ponce Dominguez
#
##############################################################################

from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.tools.misc import formatLang, format_date
from odoo.tools.translate import _
from odoo.tools import append_content_to_html, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError
from xml.dom import minidom
from xml.dom.minidom import parse, parseString

import logging
_logger = logging.getLogger(__name__)


class AccountFollowupReport(models.AbstractModel):
    _inherit = "account.followup.report"
    filter_partner_id = False

    def _get_options(self, previous_options=None):
        options = super()._get_options(previous_options)
        # It doesn't make sense to allow multicompany for these kind of reports
        # 1. Followup mails need to have the right headers from the right company
        # 2. Separation of business seems natural: a customer wouldn't know or care that the two companies are related
        if 'multi_company' in options:
            del options['multi_company']
        return options

    def _get_columns_name(self, options):
        """
        Override
        Return the name of the columns of the follow-ups report
        """
        headers = [{'name': _('No. Factura'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Fecha'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Serie Fact.'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Folio Fact.'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('F. Vencimiento'), 'class': 'date', 'style': 'text-align:center; white-space:nowrap;'},
                   # {'name': _('Comunicación'), 'style': 'text-align:right; white-space:nowrap;'},
                   # {'name': _('F. Prevista'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   # {'name': _('Excluido'), 'class': 'date', 'style': 'white-space:nowrap;'},
                   {'name': _('Total'), 'class': 'number o_price_total', 'style': 'text-align:right; white-space:nowrap;'},
                   {'name': _('Moneda'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('CP/Ejecutivo'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('CP/Ref. Cliente'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('CP/Referencia'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('Doc Origen'), 'style': 'text-align:center; white-space:nowrap;'},
                   {'name': _('CP/P. Transportado/Desc'), 'style': 'text-align:center; white-space:nowrap;'},
                  ]
        if self.env.context.get('print_mode'):
            headers = headers[:5] + headers[7:]  # Remove the 'Expected Date' and 'Excluded' columns
        return headers

    def _get_lines(self, options, line_id=None):
        """
        Override
        Compute and return the lines of the columns of the follow-ups report.
        """
        # Get date format for the lang
        partner = options.get('partner_id') and self.env['res.partner'].browse(options['partner_id']) or False
        if not partner:
            return []
        lang_code = partner.lang or self.env.user.lang or 'en_US'

        lines = []
        res = {}
        today = fields.Date.today()
        line_num = 0
        for l in partner.unreconciled_aml_ids.filtered(lambda l: l.company_id == self.env.user.company_id):
            if l.company_id == self.env.user.company_id:
                if self.env.context.get('print_mode') and l.blocked:
                    continue
                currency = l.currency_id or l.company_id.currency_id
                if currency not in res:
                    res[currency] = []
                res[currency].append(l)
        for currency, aml_recs in res.items():
            total = 0
            total_issued = 0
            for aml in aml_recs:
                amount = aml.amount_residual_currency if aml.currency_id else aml.amount_residual
                date_due = format_date(self.env, aml.date_maturity or aml.date, lang_code=lang_code)
                total += not aml.blocked and amount or 0
                is_overdue = today > aml.date_maturity if aml.date_maturity else today > aml.date
                is_payment = aml.payment_id
                if is_overdue or is_payment:
                    total_issued += not aml.blocked and amount or 0
                if is_overdue:
                    date_due = {'name': date_due, 'class': 'color-red date', 'style': 'white-space:nowrap;text-align:center;color: red;'}
                if is_payment:
                    date_due = ''
                move_line_name = aml.invoice_id.name or aml.name
                if self.env.context.get('print_mode'):
                    move_line_name = {'name': move_line_name, 'style': 'text-align:right; white-space:normal;'}
                amount = formatLang(self.env, amount, currency_obj=currency)
                line_num += 1
                expected_pay_date = format_date(self.env, aml.expected_pay_date, lang_code=lang_code) if aml.expected_pay_date else ''

                invoice_br = aml.invoice_id
                waybil_br = False
                transport_product = False
                if invoice_br.waybill_ids:
                    waybil_br = invoice_br.waybill_ids[0]
                if invoice_br.waybill_shipped_ids:
                    transport_product = invoice_br.waybill_shipped_ids[0] 

                sat_serie = invoice_br.sat_serie if invoice_br.sat_serie else ""
                sat_folio = invoice_br.sat_folio if invoice_br.sat_folio else ""
                if not sat_serie or not sat_folio:
                    xml_data = invoice_br._get_xml_file_content()
                    if xml_data:
                        arch_xml = parseString(xml_data)
                        xvalue = arch_xml.getElementsByTagName('tfd:TimbreFiscalDigital')[0]
                        yvalue = arch_xml.getElementsByTagName('cfdi:Comprobante')[0]                    
                        timbre = xvalue.attributes['UUID'].value
                        serie, folio = False, False
                        try:
                            sat_serie = yvalue.attributes['Serie'].value
                        except:
                            pass
                        try:
                            sat_folio = yvalue.attributes['Folio'].value
                        except:
                            pass

                columns = [
                    format_date(self.env, aml.date, lang_code=lang_code),
                    sat_serie or  "",
                    sat_folio or  "",
                    date_due,
                    # move_line_name,
                    # expected_pay_date + ' ' + (aml.internal_note or ''),
                    # {'name': aml.blocked, 'blocked': aml.blocked},
                    amount,
                    aml.invoice_id.currency_id.name,
                    waybil_br.x_ejecutivo if waybil_br else "",
                    waybil_br.client_order_ref if waybil_br else "",
                    waybil_br.x_reference if waybil_br else "",
                    aml.invoice_id.origin,
                    transport_product.product_id.name if transport_product else "",
                ]
                if self.env.context.get('print_mode'):
                    columns = columns[:4] + columns[6:]
                lines.append({
                    'id': aml.id,
                    'invoice_id': aml.invoice_id.id,
                    'view_invoice_id': self.env['ir.model.data'].get_object_reference('account', 'invoice_form')[1],
                    'account_move': aml.move_id,
                    'name': aml.move_id.name,
                    'caret_options': 'followup',
                    'move_id': aml.move_id.id,
                    'type': is_payment and 'payment' or 'unreconciled_aml',
                    'unfoldable': False,
                    'has_invoice': bool(aml.invoice_id),
                    'columns': [type(v) == dict and v or {'name': v} for v in columns],
                })
            total_due = formatLang(self.env, total, currency_obj=currency)
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': 'total',
                'unfoldable': False,
                'level': 0,
                'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [total >= 0 and _('Total Due') or '', total_due]],
            })
            if total_issued > 0:
                total_issued = formatLang(self.env, total_issued, currency_obj=currency)
                line_num += 1
                lines.append({
                    'id': line_num,
                    'name': '',
                    'class': 'total',
                    'unfoldable': False,
                    'level': 0,
                    'columns': [{'name': v} for v in [''] * (3 if self.env.context.get('print_mode') else 5) + [_('Total Overdue'), total_issued]],
                })
            # Add an empty line after the total to make a space between two currencies
            line_num += 1
            lines.append({
                'id': line_num,
                'name': '',
                'class': '',
                'unfoldable': False,
                'level': 0,
                'columns': [{} for col in columns],
            })
        # Remove the last empty line
        if lines:
            lines.pop()
        return lines