# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.http import route, request
import xlwt
import io
#import StringIO
import lxml.html
import base64
import logging
_logger = logging.getLogger(__name__)

def get_xls(rec):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Hoja 1')
    
    style_number = xlwt.XFStyle()
    style_number.num_format_str = '#,##0.00'
    
    
    style_title = xlwt.easyxf('font: bold 1,height 320;')
    style_subtitle = xlwt.easyxf('font: bold 1,height 280;')
    style_concept = xlwt.easyxf('font: bold 1,height 200;align: wrap 1;')
    first_col = ws.col(1)
    first_col.width = 256 * 50 
    ws.write(1, 1, rec.company_id.name, style_title)
    ws.write(2, 1, rec.ifrs_id.title, style_subtitle)
    ws.write(3, 1, rec.fiscalyear_id.name, style_subtitle)
    if rec.report_type == 'per':
        ws.write(4, 1, 'Periodo: ' + rec.period.name, style_subtitle)
    l = 6
    if rec.columns=='2_columns':
        col2 = ws.col(2)
        col3 = ws.col(3)
        col2.width = 256 * 13 
        col3.width = 256 * 13 
        ws.write(l, 1, 'Concepto',style_concept)
        ws.write(l, 2, '···',style_concept)
        ws.write(l, 3, '···',style_concept)
        l += 1
        for ifrs_l in rec.ifrs_id.get_report_data(rec):
            if ifrs_l.get('invisible'):
                continue
            l += 1
            if ifrs_l.get('type')=='abstract':
                ws.write(l, 1, ifrs_l.get('name').upper(),style_concept)
                
            elif ifrs_l.get('type') in ('detail', 'constant'):
                ws.write(l, 1, ifrs_l.get('name').upper(), style_concept)
                ws.write(l,2, ifrs_l.get('amount',0),style_number)
            
            elif ifrs_l.get('type')=='total':
                ws.write(l, 1, ifrs_l.get('name').upper(), style_concept)
                if ifrs_l.get('comparison') in ('subtract', 'ratio', 'without', False):
                    if ifrs_l.get('operator') in ('subtract', 'ratio', 'without', 'product', False):
                        ws.write(l,3, ifrs_l.get('amount',0),style_number)
                    elif ifrs_l.get('operator')== 'percent':
                        ws.write(l,3, ifrs_l.get('amount',0),style_number)
                elif ifrs_l.get('comparison')== 'percent':
                    ws.write(l,3, ifrs_l.get('amount',0),style_number)

    elif rec.columns=='12_columns':
        for x in range(1,13):
            col = ws.col(x+1)
            col.width = 256 * 13 
        ws.write(l, 1, 'Concepto',style_concept)
        ws.write(l, 2, 'Enero',style_concept)
        ws.write(l, 3, 'Febrero',style_concept)
        ws.write(l, 4, 'Marzo',style_concept)
        ws.write(l, 5, 'Abril',style_concept)
        ws.write(l, 6, 'Mayo',style_concept)
        ws.write(l, 7, 'Junio',style_concept)
        ws.write(l, 8, 'Julio',style_concept)
        ws.write(l, 9, 'Agosto',style_concept)
        ws.write(l, 10, 'Septiembre',style_concept)
        ws.write(l, 11, 'Octubre',style_concept)
        ws.write(l, 12, 'Noviemre',style_concept)
        ws.write(l, 13, 'Diciembre',style_concept)
        l += 1

        for ifrs_l in rec.ifrs_id.get_report_data(rec):
            if ifrs_l.get('invisible'):
                continue
            l += 1
            
            if ifrs_l.get('type')=='abstract':
                ws.write(l, 1, ifrs_l.get('name').upper(), style_concept)
                
            elif ifrs_l.get('type') in ('detail', 'constant'):
                ws.write(l, 1, ifrs_l.get('name').upper(), style_concept)
                for month in range(1,13):
                    ws.write(l,month+1, ifrs_l['period'][month] or 0, style_number)
            
            elif ifrs_l.get('type')=='total':
                ws.write(l, 1, ifrs_l.get('name').upper(), style_concept)
                if ifrs_l.get('comparison') in ('subtract', 'ratio', 'without', False):
                    if ifrs_l.get('operator') in ('subtract', 'ratio', 'without', 'product', False):
                        for month in range(1,13):
                            ws.write(l,month+1, ifrs_l['period'][month] or 0, style_number)
                    elif ifrs_l.get('operator')== 'percent':
                        for month in range(1,13):
                            ws.write(l,month+1, ifrs_l['period'][month] or 0, style_number)
                elif ifrs_l.get('comparison')== 'percent':
                    for month in range(1,13):
                        ws.write(l,month+1, ifrs_l['period'][month] or 0, style_number)
    
    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()




class IfrsReportWizard(models.TransientModel):
    """
    This wizard allows to print report from templates for two or twelve columns
    let that be pdf or xls file.
    """

    _name = 'ifrs.report.wizard'
    _description = 'IFRS Report Wizard'
    _rec_name = 'ifrs_id'

    @api.multi
    def _default_ifrs(self):
        ctx = self._context
        res = False
        if ctx.get('active_id') and ctx.get('active_model') == 'ifrs.ifrs':
            return ctx.get('active_id')
        return res

    @api.multi
    def _default_fiscalyear(self):
        return self.env['account.fiscalyear'].find()

    @api.multi
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    ifrs_id = fields.Many2one(
        'ifrs.ifrs', string='Plantilla de Reporte NIIF',
        default=_default_ifrs,
        required=True)
    period = fields.Many2one(
        'account.period', string='Forzar periodo',
        help=('Periodo Fiscal a usar para el Reporte'))
    fiscalyear_id = fields.Many2one(
        'account.fiscalyear', string='Año Fiscal',
        default=_default_fiscalyear)
    company_id = fields.Many2one(
        'res.company', string='Compañía',
        ondelete='cascade', required=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'ifrs.ifrs'))
    currency_id = fields.Many2one(
        'res.currency', string='Moneda',
        ondelete='cascade', required=True,
        default=_default_currency,
        help=('Moneda en la que se expresarán los montos del reporte. Si se deja vacío se toma la Moneda por defecto de la Compañía'))
    exchange_date = fields.Date(
        string='Fecha para TC',
        default=fields.Date.context_today,
        help=('Fecha a usar para el Tipo de Cambio (en caso de que la Moneda sea diferente a la Moneda de la Compañía'))
    report_type = fields.Selection(
        [('all', 'Todo el Año Fiscal'),
         ('per', 'Periodo')],
        string='Tipo', required=True,
        default='all',
        help=('Indica si el reporte será de todo el Año Fiscal o solo de un Periodo en particular'))
    columns = fields.Selection(
        [('2_columns', 'A dos Columnas'),
         ('12_columns', 'A doce Columnas')],
         #('webkitaccount.ifrs_12', 'Doce Columnas')],
        string='Número de Columnas', required=True,
        default='2_columns',
        help=('Número de Columnas que serán mostradas en el reporte:'
              ' -Dos Columnas(02),-Doce Columnas(12)'))
    target_move = fields.Selection(
        [('posted', 'Todas las pólizas Confirmadas'),
         ('all', 'Todas las pólizas (Confirmadas o No)')],
        string='Pólizas a tomar',
        default='posted')
    report_format = fields.Selection(
        [('preview', 'Vista Previa'),
         ('pdf', 'PDF'),
         ('spreadsheet', 'Hoja de Cálculo')],
        string='Salida del Reporte',
        default='preview')

    spreadsheet_file = fields.Binary(string="Descargar Archivo", readonly=True)
    spreadsheet_file_name = fields.Char(string="Nombre Archivo", readonly=True)
    
    
    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type == 'all':
            self.period = False 
        else:
            self.columns = '2_columns'

    @api.multi
    def _reopen_wizard(self):
        return { 'type'     : 'ir.actions.act_window',
                 'res_id'   : self.id,
                 'view_mode': 'form',
                 'view_type': 'form',
                 'res_model': 'ifrs.report.wizard',
                 'target'   : 'new',
                 'name'     : 'Reporte NIFF'}
            
    
    
    def get_datas(self):
        datas = {
            'wizard_id' : self.id,
            'report_type': str(self.report_type),
            'company' : self.company_id.id,
            'target_move' : self.target_move,
            'exchange_date' : self.exchange_date,
            'currency_wizard' : self.currency_id.id,
            'currency_wizard_name' : self.currency_id.name,
            'fiscalyear' : self.fiscalyear_id.id,
            'xls_report' :  False,
            'discard_logo_check': True,
        }
        if self.report_type == 'all':            
            datas['period'] = False
        else:
            datas['period'] = self.period.id

        return datas
        
    
    @api.multi
    def print_report(self):
        context = dict(self._context.copy())
        context.update({
            'active_model': 'ifrs.ifrs',
            'active_ids': [self.ifrs_id.id], 
            'fiscalyear':  self.fiscalyear_id.id,
            'active_id': self.ifrs_id.id ,
            })
        context.update(self.get_datas())
        
        
        if self.report_format == 'preview':
            if self.columns=='12_columns':
                return self.env.ref('ifrs_report.ifrs_landscape_pdf_report_action_html').with_context(context).report_action(self)
            else:
                return self.env.ref('ifrs_report.ifrs_portrait_pdf_report_action_html').with_context(context).report_action(self)
        if self.report_format == 'spreadsheet':
            context['xls_report'] = True
            if self.columns=='12_columns':
                
                html1, html2 = self.env.ref('ifrs_report.ifrs_landscape_pdf_report_action').with_context(context).render_qweb_html(self.ids)
            else:
                html1, html2 = self.env.ref('ifrs_report.ifrs_portrait_pdf_report_action').with_context(context).render_qweb_html(self.ids)
            
            
            xls_stream = get_xls(self)            
            self.write({'spreadsheet_file': base64.encodestring(xls_stream), 'spreadsheet_file_name': self.ifrs_id.name.replace(' ','_') + '.xls'})
            return self._reopen_wizard()

        # This method will do a better job than me at arranging a dictionary to
        if self.columns=='12_columns':
            return self.env.ref('ifrs_report.ifrs_landscape_pdf_report_action').with_context(context).report_action(self)
        else:
            return self.env.ref('ifrs_report.ifrs_portrait_pdf_report_action').with_context(context).report_action(self)
