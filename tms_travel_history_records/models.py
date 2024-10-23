# -*- encoding: utf-8 -*-
### <German Ponce Dominguez>

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError

#### Gestión Zona Horaria ####

from datetime import datetime
from pytz import timezone
import pytz
import time
from datetime import timedelta

#### Gestión del Excel ####

import xlwt
from io import BytesIO
import base64

from itertools import zip_longest

##########################


class TMSTravelHistoryEvents(models.Model):
    _name = 'tms.travel.history.events'
    _description = 'Historial de viaje y eventos'
    _order = "id desc"
    @api.depends('travel_id.current_waybill_ids')
    def _get_x_reference(self):
        for rec in self:
            x_reference_full = ""
            if rec.travel_id.current_waybill_ids:
                for waybill in rec.travel_id.current_waybill_ids:
                    waybill_x_ref = waybill.x_reference
                    if not waybill_x_ref:
                        waybill_x_ref = waybill.name
                    x_reference_full = x_reference_full+', '+waybill_x_ref if x_reference_full else x_reference_full+waybill_x_ref
            rec.x_reference = x_reference_full

    def _get_current_date_time(self):

        return str(fields.Datetime.now())[0:19]

    def _get_current_user(self):
        return self.env.user.id

    user_id = fields.Many2one('res.users', 'Usuario', default=_get_current_user)
    name = fields.Char('Comentarios', size=128)
    travel_id = fields.Many2one('tms.travel', 'Viaje')

    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehiculo', related="travel_id.vehicle_id", store=True)
    employee_id = fields.Many2one('hr.employee', 'Conductor', related="travel_id.employee_id", store=True)
    partner_id = fields.Many2one('res.partner', 'Cliente', related="travel_id.partner_id", store=True)
    x_reference = fields.Char('Referencia', compute="_get_x_reference", store=True)

    location = fields.Char('Ubicación', size=128, required=True)
    status = fields.Char('Status', size=128, required=True)

    date_time = fields.Datetime('Fecha/Hora', default=_get_current_date_time)

    warning = fields.Boolean('Warning')

    #### Gestión Zona Horaria ####

    def _get_date_time_report_tz(self):
        context = self._context
        res = {}
        dt_format = tools.DEFAULT_SERVER_DATETIME_FORMAT
        tz = self.env.user.tz
        if not tz:
            tz = 'Mexico/General'
        date_time_report_tz = ""
        for rec in self:
            htz_diff = rec._get_time_zone()
            date_time = rec.date_time if rec.date_time else datetime.now()
            fecha_informe = time.strftime('%Y-%m-%d %H:%M:%S', time.strptime(str(date_time)[:19], '%Y-%m-%d %H:%M:%S'))
            fecha_informe = datetime.strptime(fecha_informe, '%Y-%m-%d %H:%M:%S') + timedelta(hours=htz_diff) or False
            fecha_informe = str(fecha_informe)
            date_time_report_tz = str(fecha_informe)[0:19] if fecha_informe else False
        return date_time_report_tz


    def _get_time_zone(self):

        userstz = self.env.user.tz
        if not userstz:
            userstz = 'Mexico/General'
        a = 0
        if userstz:
            hours = timezone(userstz)
            fmt = '%Y-%m-%d %H:%M:%S %Z%z'
            now = datetime.now()
            loc_dt = hours.localize(datetime(now.year, now.month, now.day,
                                             now.hour, now.minute, now.second))
            timezone_loc = (loc_dt.strftime(fmt))
            diff_timezone_original = timezone_loc[-5:-2]
            timezone_original = int(diff_timezone_original)
            s = str(datetime.now(pytz.timezone(userstz)))
            s = s[-6:-3]
            timezone_present = int(s)*-1
            a = timezone_original + ((
                timezone_present + timezone_original)*-1)
        return a
    
    ############################          

class TMSTravel(models.Model):
    _name = 'tms.travel'
    _inherit ='tms.travel'

    travel_history_monitoring_ids = fields.One2many('tms.travel.history.events', 'travel_id', 'Historial Monitoreo')

    ### Gestión del Excel ####

    travel_history_fname = fields.Char('Nombre Archivo',size=256)

    travel_history_file = fields.Binary("Reporte")

    ##########################

    def print_history_report(self):
        return self.env.ref('tms_travel_history_records.report_tms_monitoring_history').report_action(self)


    def minitoring_to_tree_view(self):
        travel_history_monitoring_ids = self.travel_history_monitoring_ids.ids
        return {
            'domain': [('id', 'in', travel_history_monitoring_ids)],
            'name': _('Historial de Monitoreo'),
            'view_mode': 'tree,form',
            'view_type': 'form',
            'context': {'tree_view_ref': 'tms_travel_history_records.tms_travel_history_events_tree'},
            'res_model': 'tms.travel.history.events',
            'type': 'ir.actions.act_window'
            }


    #### Gestión del Excel ####

    def print_history_report_xlsx(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        file_url = base_url+"/web/content?model=tms.travel&field=travel_history_file&filename_field=travel_history_fname&id=%s&&download=true" % (self.id,)
        self.generate_report_travel_history_xlsx()
        return {
                 'type': 'ir.actions.act_url',
                 'url': file_url,
                 'target': 'new'
                }

    ############### Descarga de Plantilla Excel ##################################

    def generate_report_travel_history_xlsx(self):
        workbook = xlwt.Workbook(encoding='utf-8',style_compression=2)
        heading_format = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center')
        heading_format_left = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left')
        heading_format_center = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center')
        bold = xlwt.easyxf('font:bold True,height 215;pattern: pattern solid, fore_colour gray25;align: horiz center')
        bold_center = xlwt.easyxf('font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;')
        bold_right = xlwt.easyxf('font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz right;')
        bold_left = xlwt.easyxf('font:height 240,bold True;pattern: pattern solid, fore_colour gray25;align: horiz left;')

        ### Cutom Color Background fot Comments ####
        xlwt.add_palette_colour("gray_custom", 0x21)
        workbook.set_colour_RGB(0x21, 238, 238, 238)

        tags_data_gray = xlwt.easyxf('font:bold True,height 200;pattern: pattern solid, fore_colour gray_custom;align: horiz center')
        
        tags_data_gray_right = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray_custom;align: horiz right;')
        tags_data_gray_center = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray_custom;align: horiz center;')
        tags_data_gray_left = xlwt.easyxf('font:height 200;pattern: pattern solid, fore_colour gray_custom;align: horiz left;')
            
        

        totals_bold_right = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz right;')
        totals_bold_center = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;')
        totals_bold_left = xlwt.easyxf('font:height 200;pattern: pattern solid, fore_colour gray25;align: horiz left;')
        
        normal_center = xlwt.easyxf('align: horiz center;')
        normal_right = xlwt.easyxf('align: horiz right;')
        normal_left = xlwt.easyxf('align: horiz left;')

        normal_center_yellow = xlwt.easyxf('align: horiz center;pattern: pattern solid, fore_colour light_yellow;')
        normal_right_yellow = xlwt.easyxf('align: horiz right;pattern: pattern solid, fore_colour light_yellow;')
        normal_left_yellow = xlwt.easyxf('align: horiz left;pattern: pattern solid, fore_colour light_yellow;')

        #### Con Bordes #####
        # "borders: top double, bottom double, left double, right double;" # Como botones

        tags_data_gray_right_border = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray_custom;align: horiz right;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        tags_data_gray_center_border = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray_custom;align: horiz center;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        tags_data_gray_left_border = xlwt.easyxf('font:height 200;pattern: pattern solid, fore_colour gray_custom;align: horiz left;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        
        normal_center_yellow_border = xlwt.easyxf('align: horiz center;pattern: pattern solid, fore_colour light_yellow;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        normal_right_yellow_border = xlwt.easyxf('align: horiz right;pattern: pattern solid, fore_colour light_yellow;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        normal_left_yellow_border = xlwt.easyxf('align: horiz left;pattern: pattern solid, fore_colour light_yellow;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')

        normal_center_border = xlwt.easyxf('align: horiz center;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        normal_right_border = xlwt.easyxf('align: horiz right;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')
        normal_left_border = xlwt.easyxf('align: horiz left;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')

        normal_left_border_red = xlwt.easyxf('align: horiz left;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin; font: colour red, bold True;')

        heading_format_border = xlwt.easyxf('font:height 200,bold True;pattern: pattern solid, fore_colour gray25;align: horiz center;borders: top_color black, bottom_color black, right_color black, left_color black,\
                              left thin, right thin, top thin, bottom thin;')

        worksheet = workbook.add_sheet('Historial de Monitoreo', bold_center)
        worksheet.col(0).width  = int(40 * 260)
        worksheet.col(1).width  = int(40 * 260)
        worksheet.col(2).width  = int(18 * 260)
        worksheet.col(3).width  = int(18 * 260)
        worksheet.col(4).width  = int(40 * 260)
        worksheet.col(5).width  = int(18 * 260)
        worksheet.col(6).width  = int(40 * 260)
        worksheet.col(7).width  = int(18 * 260)
        worksheet.col(8).width  = int(18 * 260)
        worksheet.col(9).width  = int(18 * 260)
        worksheet.col(10).width = int(18 * 260)
        worksheet.col(11).width = int(18 * 260)
        worksheet.col(12).width = int(18 * 260)
        worksheet.col(13).width = int(18 * 260)
        worksheet.col(14).width = int(18 * 260)
        worksheet.col(15).width = int(18 * 260)
        worksheet.col(16).width = int(18 * 260)
        worksheet.col(17).width = int(18 * 260)
        worksheet.col(18).width = int(18 * 260)
        worksheet.col(20).width = int(18 * 260)
        worksheet.col(21).width = int(18 * 260)
        worksheet.col(22).width = int(18 * 260)

        row = 1

        ### Figuras de Transporte ###
        worksheet.write_merge(row, row, 0, 8, 'Historial de Monitoreo %s' % self.name, heading_format_center)
        row += 2
        worksheet.write(row, 0, "Usuario", tags_data_gray_center_border)
        worksheet.write(row, 1, "Vehículo", tags_data_gray_center_border)
        worksheet.write(row, 2, "Conductor", tags_data_gray_center_border)
        worksheet.write(row, 3, "Cliente", tags_data_gray_center_border)
        worksheet.write(row, 4, "Referencia", tags_data_gray_center_border)
        worksheet.write(row, 5, "Ubicación", tags_data_gray_center_border)
        worksheet.write(row, 6, "Status", tags_data_gray_center_border)
        worksheet.write(row, 7, "Comentarios", tags_data_gray_center_border)
        worksheet.write(row, 8, "Fecha/Hora", tags_data_gray_center_border)

        ### Operadores ####

        for line in self.travel_history_monitoring_ids:

            date_time = str(line._get_date_time_report_tz())[0:19]

            row += 1
            style_line_report = normal_left_border
            if line.warning:
                style_line_report = normal_left_border_red

            worksheet.write(row, 0, line.user_id.name, style_line_report)
            worksheet.write(row, 1, line.vehicle_id.name_get()[0][1], style_line_report)
            worksheet.write(row, 2, line.employee_id.name, style_line_report)
            worksheet.write(row, 3, line.partner_id.name, style_line_report)
            worksheet.write(row, 4, line.x_reference, style_line_report)
            worksheet.write(row, 5, line.location, style_line_report)
            worksheet.write(row, 6, line.status, style_line_report)
            worksheet.write(row, 7, line.name or "", style_line_report)
            worksheet.write(row, 8, date_time, style_line_report)

        travel_name = self.name.replace('/','_') if self.name else 'SN'
        filename = ('Plantilla Datos Carta Porte '+str(travel_name) + '.xls') 
        fp = BytesIO()
        workbook.save(fp)
        
        self.write({
                        'travel_history_file': base64.encodestring(fp.getvalue()),
                        'travel_history_fname': filename,
                    })
        
        fp.close()
        return True
