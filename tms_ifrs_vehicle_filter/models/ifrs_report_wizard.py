# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from openerp.http import route, request
import xlwt
## libreria XLSX
import xlsxwriter
import tempfile

import io
#import StringIO
import lxml.html
import base64

from odoo.modules import module

import logging
_logger = logging.getLogger(__name__)

def get_report_xlsx(rec):
    ####### GENERACION DEL REPORTE XLSX ########
    # Create an new Excel file and add a worksheet.
    fname=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)
    workbook = xlsxwriter.Workbook(fname)
    worksheet = workbook.add_worksheet('Analisis Unidades')

    # Widen the first column to make the text clearer.
    worksheet.set_column('A:A', 50)
    len_vehicle_ids = len(rec.vehicle_ids) + 3
    column_from_number = colnum_string(len_vehicle_ids)

    worksheet.set_column('B:%s' % column_from_number, 20)
    # Add a bold format to use to highlight cells.
    #### ESTILOS DE CELDAS #####
    bold = workbook.add_format({'bold': True})

    format_period_title = workbook.add_format({
                        'bold':     True,
                        'align':    'center',
                        'valign':   'vcenter',
                        'bg_color': '#224e70',
                        'font_color': '#FFFFFF',
                    })

    format_period_title.set_font_size(18)
    format_period_title.set_bottom(2)
    format_period_title.set_top(2)

    format_subtitles_blue_left = workbook.add_format({
                        'bold':     True,
                        'align':    'left',
                        'valign':   'vcenter',
                        'bg_color': '#82b6f1',
                    })

    format_subtitles_blue_left.set_font_size(14)
    format_subtitles_blue_left.set_border(2)
    format_subtitles_blue_left.set_border_color('#FFFFFF')

    format_subtitles_blue = workbook.add_format({
                        'bold':     True,
                        'align':    'center',
                        'valign':   'vcenter',
                        'bg_color': '#82b6f1',
                    })
    format_subtitles_blue.set_border(2)
    format_subtitles_blue.set_font_size(14)
    format_subtitles_blue.set_border_color('#FFFFFF')

    format_concept_gray = workbook.add_format({
                        'align':    'left',
                        'valign':   'vcenter',
                        'bg_color': '#dddddd',
                    })
    format_concept_gray.set_border(2)
    format_concept_gray.set_font_size(12)
    format_concept_gray.set_border_color('#FFFFFF')

    format_concept_blue = workbook.add_format({
                        'align':    'left',
                        'valign':   'vcenter',
                        'bg_color': '#82b6f1',
                        'bold': True,
                    })
    format_concept_blue.set_border(2)
    format_concept_blue.set_font_size(12)
    format_concept_blue.set_border_color('#FFFFFF')

    num_format = '#,##0.00'

    format_concept_gray_numeric = workbook.add_format({
                        'align':    'left',
                        'valign':   'vcenter',
                        'bg_color': '#dddddd',
                    })
    format_concept_gray_numeric.set_border(2)
    format_concept_gray_numeric.set_font_size(12)
    format_concept_gray_numeric.set_border_color('#FFFFFF')
    format_concept_gray_numeric.set_num_format(num_format)

    format_concept_blue_numeric = workbook.add_format({
                        'align':    'left',
                        'valign':   'vcenter',
                        'bg_color': '#82b6f1',
                        'bold': True,
                    })
    format_concept_blue_numeric.set_border(2)
    format_concept_blue_numeric.set_font_size(12)
    format_concept_blue_numeric.set_border_color('#FFFFFF')
    format_concept_blue_numeric.set_num_format(num_format)

    ### Comenzamos con el Reporte ####
    #len_vehicle_ids = len(rec.vehicle_ids) + 3
    #column_from_number = colnum_string(len_vehicle_ids)
    
    #worksheet.set_column('B:%' + column_from_number, 20)

    report_ifrs_name = rec.ifrs_id.name+'\n ( ' + str(rec.fiscalyear_id.name)+' )'

    module_path = module.get_module_path('tms_ifrs_vehicle_filter')
    image_module_path = module_path+'/images/logo_empresa.png'
    # sheet.insert_image('A2', image_module_path)

    # worksheet.merge_range('A1:B4', rec.ifrs_id.company_id.name,format_period_subtitle)
    worksheet.insert_image('A1', image_module_path)

    #worksheet.write('A1:F2', 'Plan de Cuentas', format_red)
    range_dinamic = 'A1:'+column_from_number+'5'
    indice_fila=6
    worksheet.merge_range(range_dinamic, report_ifrs_name,format_period_title)

    ### Comenzamos a Ingresar las Unidades ###
    ### Titulos de los Conceptos del Reporte ####
    column_number = 1
    indice_header_vehicles = indice_fila
    column_name = colnum_string(column_number)
    worksheet.write(str(column_name)+str(indice_fila), '...',format_subtitles_blue_left)

    ## Incrementamos el Indice Para comenzar a Insertar los Valores ##
    indice_fila += 1
    ### Duplicamos el Indice para tener un Indice Temporal ####
    indice_fila_tmp = indice_fila

    column_dict_position_concept_report = { }
    column_dict_position_concepts_total = { }

    for ifrs_l in rec.ifrs_id.get_report_headers_blchz(rec):
      column_dict_position_concept_report.update({
        ifrs_l['id']: {
                        'posicion_indice_fila': indice_fila_tmp, 
                        'name': ifrs_l['name'],
                        'invisible': ifrs_l['invisible'],
                        'type': ifrs_l['type'],
                        'total_acumulativo': 0.0, 
                        }
        })
      if ifrs_l['type'] == 'total':
        worksheet.write(str(column_name)+str(indice_fila_tmp), ifrs_l.get('name').upper(),format_concept_blue)


      else:
        worksheet.write(str(column_name)+str(indice_fila_tmp), ifrs_l.get('name').upper(),format_concept_gray)
      indice_fila_tmp += 1
    ### Incremento de la Columna
    column_number += 1
    column_dict_position_vehicle = { }
    for vehicle in rec.vehicle_ids:
      column_name = colnum_string(column_number)
      column_dict_position_vehicle.update({
        vehicle: str(column_name),
        })
      worksheet.write(str(column_name)+str(indice_header_vehicles), vehicle.name2,format_subtitles_blue)

      for ifrs_lv in rec.ifrs_id.get_report_data_vehicle_select(rec, vehicle):
        ifrs_concept_id = ifrs_lv['id']
        ifrs_concept_total = ifrs_lv['amount']
        indice_to_concept = 150
        if ifrs_lv['type'] == 'total':
          indice_to_concept = column_dict_position_concept_report[ifrs_concept_id]['posicion_indice_fila']
          #### Escribimos el Resultado ##### 
          worksheet.write(str(column_name)+str(indice_to_concept), ifrs_concept_total,format_concept_blue_numeric)
        else:
          indice_to_concept = column_dict_position_concept_report[ifrs_concept_id]['posicion_indice_fila']
          #### Escribimos el Resultado ##### 
          worksheet.write(str(column_name)+str(indice_to_concept), ifrs_concept_total,format_concept_gray_numeric)

        ### Guardamos los Totales Para Escribirlos en la Ultima Columna Total ####
        indice_to_concept_total_sumatory = column_dict_position_concept_report[ifrs_concept_id]['total_acumulativo']
        indice_to_concept_total_sumatory += ifrs_concept_total
        column_dict_position_concept_report[ifrs_concept_id].update({'total_acumulativo': indice_to_concept_total_sumatory})
      ## Incrementamos el nombre de la columna #
      column_number += 1

    ### Calculamos los Montos del Reporte de lo que no contiene Unidades. ####
    column_name = colnum_string(column_number)
    worksheet.write(str(column_name)+str(indice_header_vehicles), 'Sin Vehículo',format_subtitles_blue)
    ## Incrementamos el nombre de la columna #
    for ifrs_nv in rec.ifrs_id.get_report_data_no_vehicles(rec):
      ifrs_no_vehicle_id = ifrs_nv['id']
      ifrs_no_vehicle_total = ifrs_nv['amount']
      indice_to_concept = 150
      if ifrs_nv['type'] == 'total':
        indice_to_concept = column_dict_position_concept_report[ifrs_no_vehicle_id]['posicion_indice_fila']
        #### Escribimos el Resultado ##### 
        worksheet.write(str(column_name)+str(indice_to_concept), ifrs_no_vehicle_total,format_concept_blue_numeric)
      else:
        indice_to_concept = column_dict_position_concept_report[ifrs_no_vehicle_id]['posicion_indice_fila']
        #### Escribimos el Resultado ##### 
        worksheet.write(str(column_name)+str(indice_to_concept), ifrs_no_vehicle_total,format_concept_gray_numeric)

      ### Guardamos los Totales Para Escribirlos en la Ultima Columna Total ####
      indice_to_no_vehicle_total_sumatory = column_dict_position_concept_report[ifrs_no_vehicle_id]['total_acumulativo']
      indice_to_no_vehicle_total_sumatory += ifrs_no_vehicle_total
      column_dict_position_concept_report[ifrs_no_vehicle_id].update({'total_acumulativo': indice_to_no_vehicle_total_sumatory})

    column_number += 1


    ### Aqui Escribimos la Columna de los Totales ####
    column_name = colnum_string(column_number)
    worksheet.write(str(column_name)+str(indice_header_vehicles), 'TOTAL',format_subtitles_blue)
    ## Incrementamos el nombre de la columna #
    for ifrs_total_id in column_dict_position_concept_report.keys():
      ifrs_total_vals = column_dict_position_concept_report[ifrs_total_id]
      ifrs_total_acumulativo = ifrs_total_vals['total_acumulativo']
      indice_to_concept = 150
      if ifrs_total_vals['type'] == 'total':
        indice_to_concept = ifrs_total_vals['posicion_indice_fila']
        #### Escribimos el Resultado ##### 
        worksheet.write(str(column_name)+str(indice_to_concept), ifrs_total_acumulativo,format_concept_blue_numeric)
      else:
        indice_to_concept = ifrs_total_vals['posicion_indice_fila']
        #### Escribimos el Resultado ##### 
        worksheet.write(str(column_name)+str(indice_to_concept), ifrs_total_acumulativo,format_concept_gray_numeric)

    column_number += 1

    ## Incrementamos el nombre de la columna #
    column_number += 1

    # print ("### column_dict_position_vehicle >>>> ",column_dict_position_vehicle)
    ## Al Terminar de Escribir los Headers Incrementamos la Fila ##
    indice_fila += 1

    #for vehicle in rec.vehicle_ids:


    workbook.close()

    file_result = open(fname.name, 'rb').read()

    return file_result

def colnum_string(n):
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string


def get_xls(rec):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Hoja 1')
    style_number = xlwt.XFStyle()
    style_number.num_format_str = '#,##0.00'
    
    style_number_back_gray = xlwt.XFStyle()
    style_number_back_gray.num_format_str = '#,##0.00'
    style_number_back_gray.color = 'black' 

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
                        ws.write(l,3, ifrs_l.get('amount',0),style_number_back_gray)
                    elif ifrs_l.get('operator')== 'percent':
                        ws.write(l,3, ifrs_l.get('amount',0),style_number_back_gray)
                elif ifrs_l.get('comparison')== 'percent':
                    ws.write(l,3, ifrs_l.get('amount',0),style_number_back_gray)

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
    xls_res = stream.getvalue()
    return xls_res

class IfrsReportWizard(models.TransientModel):
    _inherit = 'ifrs.report.wizard'
    
    @api.model  
    def default_get(self, fields):
        res = super(sale_order_invoice_wizard, self).default_get(fields)
        record_ids = self._context.get('active_ids', [])
        ifrs_ifrsr_obj = self.env['ifrs.ifrs']
        if not record_ids:
            return {}
        for ifrs in ifrs_ifrsr_obj.browse(record_ids):
            if ifrs.title.upper() == 'ESTADO DE RESULTADOS':
                res.update(is_edo_results=True)
        return res


    is_edo_results = fields.Boolean('Es un estado de resultados')

    store_ids = fields.Many2many('res.store', 'account_mx_ifrs_stores_wizard_rel', 'ifrs_wizard_id', 
                                   'store_id', 'Sucursales', required=False)


    vehicle_ids = fields.Many2many('fleet.vehicle', 'account_mx_ifrs_vehicle_rel', 'ifrs_wizard_id', 
                                   'vehicle_id', 'Vehículos', required=False)
    
    show_report_format2 = fields.Boolean('Reporte Edo. Resultados Belchez')
    report_format2 = fields.Selection(
        [('preview', 'Vista Previa'),
         ('pdf', 'PDF'),
         ('spreadsheet', 'Hoja de Cálculo')],
        string='Salida del Reporte',
        default='preview')

    columns2 = fields.Selection(
        [('2_columns', 'A dos Columnas'),
         ('12_columns', 'A doce Columnas')],
         #('webkitaccount.ifrs_12', 'Doce Columnas')],
        string='Número de Columnas', required=True,
        default='2_columns',
        help=('Número de Columnas que serán mostradas en el reporte:'
              ' -Dos Columnas(02),-Doce Columnas(12)'))

    def get_datas(self):
        datas = super(IfrsReportWizard, self).get_datas()
        
        if self.vehicle_ids: # Para modulo tms_ifrs_vehicle_filter
            datas.update({'vehicle_names' : ','.join([w.name2 for w in self.vehicle_ids]),
                          'vehicle_ids' : self.vehicle_ids.ids,
                         })
        return datas


    @api.model
    def default_get(self, pfields):
        """
        Get list of bills to pay
        """
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')

        # Checks on received invoice records
        records_browse = self.env[active_model].browse(active_ids)
        
        res = super(IfrsReportWizard, self).default_get(pfields)
        if records_browse[0].reporte_belchez_edo:
          show_report_format2 = True
          report_format  = 'spreadsheet'
          report_format2  = 'spreadsheet'
          columns = '2_columns'
          columns2 = '2_columns'
          res.update({
              'show_report_format2': show_report_format2,
              'report_format': report_format,
              'report_format2': report_format2,
              'columns': columns,
              'columns2':columns2 ,
            })
        return res


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
            
            if self.show_report_format2:
              if not self.vehicle_ids:
                return self.env.ref('ifrs_report.ifrs_portrait_pdf_report_action').with_context(context).report_action(self)
                # raise UserError("No se ha seleccionado ningun Vehiculo.")
                # xls_stream = get_xls(self)            
                # self.write({'spreadsheet_file': base64.encodestring(xls_stream), 'spreadsheet_file_name': self.ifrs_id.name.replace(' ','_') + '.xls'})
              else:
                xlsx_stream = get_report_xlsx(self)
                self.write({'spreadsheet_file': base64.encodestring(xlsx_stream), 'spreadsheet_file_name': self.ifrs_id.name.replace(' ','_') + '.xlsx'})
            else:
              xls_stream = get_xls(self)            
              self.write({'spreadsheet_file': base64.encodestring(xls_stream), 'spreadsheet_file_name': self.ifrs_id.name.replace(' ','_') + '.xls'})
            
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            file_url = base_url+"/web/content?model=ifrs.report.wizard&field=spreadsheet_file&filename_field=spreadsheet_file_name&id=%s&&download=true" % (self.id,)

            return {
                     'type': 'ir.actions.act_url',
                     'url': file_url,
                     'target': 'new'
                    } 

            #return self._reopen_wizard()


        # This method will do a better job than me at arranging a dictionary to
        if self.columns=='12_columns':
            return self.env.ref('ifrs_report.ifrs_landscape_pdf_report_action').with_context(context).report_action(self)
        else:
            return self.env.ref('ifrs_report.ifrs_portrait_pdf_report_action').with_context(context).report_action(self)


class IfrsIfrs(models.Model):
    _name = 'ifrs.ifrs'
    _inherit ='ifrs.ifrs'

    reporte_belchez_edo = fields.Boolean('Estado Resultados Belchez ', help='Este campo permite generar un \
      Reporte de Estado de Resultados en un formato especial, ordenando las Columnas de forma Independiente \
      por Vehiculo hacia la derecha.' )


    @api.multi
    def get_report_data_vehicle_select(self, wizard, vehicle):#, fiscalyear=None, exchange_date=None,
                              #currency_wizard=None, target_move=None, period=None, two=None):
        self.ensure_one()
        ctx = self.env.context.copy()
        if 'vehicle_ids' in wizard._fields and wizard.vehicle_ids: # Para modulo tms_ifrs_vehicle_filter
            ctx.update({'vehicle_names' : ','.join([w.name2 for w in wizard.vehicle_ids]),
                        'vehicle_ids'   : [vehicle.id]})

        ctx.update({'report_type'   : str(wizard.report_type),
                    'company'       : wizard.company_id.id,
                    'target_move'   : wizard.target_move,
                    'exchange_date' : wizard.exchange_date,
                    'currency_wizard': wizard.currency_id.id,
                    'currency_wizard_name' : self.currency_id.name,
                    'fiscalyear'    : wizard.fiscalyear_id.id,
                    'period'        : False if wizard.report_type == 'all' else wizard.period.id })

        
        
        data = []
        ifrs_line = self.env['ifrs.lines']
        period_name = self._get_periods_name_list(wizard.fiscalyear_id.id)
        ordered_lines = self._get_ordered_lines()
        bag = {}.fromkeys(ordered_lines, None)

        # TODO: THIS Conditional shall reduced
        one_per = bool(wizard.period) #  is not None

        for il_id in ordered_lines:
            ifrs_l = ifrs_line.browse(il_id)
            bag[ifrs_l.id] = {}

            line = {
                'sequence'  : int(ifrs_l.sequence),
                'id'        : ifrs_l.id,
                'name'      : ifrs_l.name,
                'invisible' : ifrs_l.invisible,
                'type'      : str(ifrs_l.type),
                'comparison': ifrs_l.comparison,
                'operator'  : ifrs_l.operator}

            if wizard.columns=='2_columns': #two:
                report_total_amount = ifrs_l._get_amount_with_operands(
                    ifrs_l, period_name, 
                    wizard.fiscalyear_id.id, wizard.exchange_date, 
                    wizard.currency_id.id, False if wizard.report_type == 'all' else wizard.period.id, 
                    wizard.target_move, two=True, 
                    one_per=one_per, bag=bag,
                    data=ctx)
                line['amount'] = report_total_amount
            else:
                line['period'] = ifrs_l.with_context(ctx)._get_dict_amount_with_operands(
                    ifrs_l, period_name, 
                    wizard.fiscalyear_id.id, wizard.exchange_date, 
                    wizard.currency_id.id, None, 
                    wizard.target_move, two=False, 
                     bag=bag, data=ctx)

            # NOTE:Only lines from current Ifrs report record are taken into
            # account given there are lines included from other reports to
            # compute values
            if ifrs_l.ifrs_id.id == self.id:
                data.append(line)
        data.sort(key=lambda x: int(x['sequence']))
        return data


    @api.multi
    def get_report_headers_blchz(self, wizard):#, fiscalyear=None, exchange_date=None,
                              #currency_wizard=None, target_move=None, period=None, two=None):

        self.ensure_one()
        ctx = self.env.context.copy()

        if 'vehicle_ids' in wizard._fields and wizard.vehicle_ids: # Para modulo tms_ifrs_vehicle_filter
            ctx.update({'vehicle_names' : ','.join([w.name2 for w in wizard.vehicle_ids]),
                        'vehicle_ids'   : wizard.vehicle_ids.ids})

        ctx.update({'report_type'   : str(wizard.report_type),
                    'company'       : wizard.company_id.id,
                    'target_move'   : wizard.target_move,
                    'exchange_date' : wizard.exchange_date,
                    'currency_wizard': wizard.currency_id.id,
                    'currency_wizard_name' : self.currency_id.name,
                    'fiscalyear'    : wizard.fiscalyear_id.id,
                    'period'        : False if wizard.report_type == 'all' else wizard.period.id })      
        
        data = []
        ifrs_line = self.env['ifrs.lines']
        period_name = self._get_periods_name_list(wizard.fiscalyear_id.id)
        ordered_lines = self._get_ordered_lines()
        bag = {}.fromkeys(ordered_lines, None)

        # TODO: THIS Conditional shall reduced
        one_per = bool(wizard.period) #  is not None

        for il_id in ordered_lines:
            ifrs_l = ifrs_line.browse(il_id)
            bag[ifrs_l.id] = {}

            line = {
                'sequence'  : int(ifrs_l.sequence),
                'id'        : ifrs_l.id,
                'name'      : ifrs_l.name,
                'invisible' : ifrs_l.invisible,
                'type'      : str(ifrs_l.type),
                'comparison': ifrs_l.comparison,
                'operator'  : ifrs_l.operator}
            # NOTE:Only lines from current Ifrs report record are taken into
            # account given there are lines included from other reports to
            # compute values
            if ifrs_l.ifrs_id.id == self.id:
                data.append(line)
        data.sort(key=lambda x: int(x['sequence']))
        return data

    @api.multi
    def get_report_data_no_vehicles(self, wizard):
        self.ensure_one()
        ctx = self.env.context.copy()

        if 'vehicle_ids' in wizard._fields and wizard.vehicle_ids: # Para modulo tms_ifrs_vehicle_filter
            ctx.update({'vehicle_names' : ','.join([w.name2 for w in wizard.vehicle_ids]),
                        'operator_vehicle'   : 'vehicle_null',
                        'vehicle_ids'   : wizard.vehicle_ids.ids})
            # ctx.update({'vehicle_names' : ','.join([w.name2 for w in wizard.vehicle_ids]),
            #             'operator_vehicle'   : 'NOT IN',
            #             'vehicle_ids'   : wizard.vehicle_ids.ids})

        ctx.update({'report_type'   : str(wizard.report_type),
                    'company'       : wizard.company_id.id,
                    'target_move'   : wizard.target_move,
                    'exchange_date' : wizard.exchange_date,
                    'currency_wizard': wizard.currency_id.id,
                    'currency_wizard_name' : self.currency_id.name,
                    'fiscalyear'    : wizard.fiscalyear_id.id,
                    'period'        : False if wizard.report_type == 'all' else wizard.period.id })

        
        
        data = []
        ifrs_line = self.env['ifrs.lines']
        period_name = self._get_periods_name_list(wizard.fiscalyear_id.id)
        ordered_lines = self._get_ordered_lines()
        bag = {}.fromkeys(ordered_lines, None)

        # TODO: THIS Conditional shall reduced
        one_per = bool(wizard.period) #  is not None

        for il_id in ordered_lines:
            ifrs_l = ifrs_line.browse(il_id)
            bag[ifrs_l.id] = {}

            line = {
                'sequence'  : int(ifrs_l.sequence),
                'id'        : ifrs_l.id,
                'name'      : ifrs_l.name,
                'invisible' : ifrs_l.invisible,
                'type'      : str(ifrs_l.type),
                'comparison': ifrs_l.comparison,
                'operator'  : ifrs_l.operator}

            if wizard.columns=='2_columns': #two:
                line['amount'] = ifrs_l._get_amount_with_operands(
                    ifrs_l, period_name, 
                    wizard.fiscalyear_id.id, wizard.exchange_date, 
                    wizard.currency_id.id, False if wizard.report_type == 'all' else wizard.period.id, 
                    wizard.target_move, two=True, 
                    one_per=one_per, bag=bag,
                    data=ctx)
            else:
                line['period'] = ifrs_l.with_context(ctx)._get_dict_amount_with_operands(
                    ifrs_l, period_name, 
                    wizard.fiscalyear_id.id, wizard.exchange_date, 
                    wizard.currency_id.id, None, 
                    wizard.target_move, two=False, 
                     bag=bag, data=ctx)

            # NOTE:Only lines from current Ifrs report record are taken into
            # account given there are lines included from other reports to
            # compute values
            if ifrs_l.ifrs_id.id == self.id:
                data.append(line)
        data.sort(key=lambda x: int(x['sequence']))
        return data
