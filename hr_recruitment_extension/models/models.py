# -*- coding: utf-8 -*-

from odoo import models, fields, api

from odoo.exceptions import UserError

### Modelos Nuevos ###
import pytz

# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
_tzs = [(tz, tz) for tz in sorted(pytz.all_timezones, key=lambda tz: tz if not tz.startswith('Etc/') else '_')]
def _tz_get(self):
    return _tzs

class HrEmployeeAptitud(models.Model):
    _name = 'hr.employee.aptitud'

    name = fields.Char('Descripción', size=64)

class HrEmployeeTipoLicencia(models.Model):
    _name = 'hr.employee.tipo.licencia'

    name = fields.Char('Tipo Licencia', size=64)

class CreateEmployeeWizard(models.TransientModel):
    _name = 'create.employee.wizard'
    _description = 'Crear Empleado desde Reclutamiento'
    
    @api.depends('no_licencia_stop')
    def _get_days(self):
        for rec in self:
            if not rec.no_licencia_stop:
                rec.no_licencia_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.no_licencia_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.no_licencia_days_to = total_days if total_days > 0 else 0

    @api.depends('ex_medic_stop')
    def _get_days_ex_medic(self):
        for rec in self:
            if not rec.ex_medic_stop:
                rec.ex_medic_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.ex_medic_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.ex_medic_days_to = total_days if total_days > 0 else 0

    @api.depends('r_control_stop')
    def _get_days_r_control(self):
        for rec in self:
            if not rec.r_control_stop:
                rec.r_control_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_days_to = total_days if total_days > 0 else 0


    @api.depends('r_control_gafete_stop')
    def _get_days_r_control_gafete(self):
        for rec in self:
            if not rec.r_control_gafete_stop:
                rec.r_control_gafete_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_gafete_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_gafete_days_to = total_days if total_days > 0 else 0

    @api.model  
    def default_get(self, fields):
        res = super(CreateEmployeeWizard, self).default_get(fields)
        hr_app_obj = self.env['hr.applicant']
        data_update = {}
        context = self._context
        for hrapp in hr_app_obj.browse(context.get('active_ids')):
            data_update = {
                            'no_ex_medico': hrapp.no_ex_medico,
                            'aptitud_id': hrapp.aptitud_id.id if hrapp.aptitud_id else False,
                            'ex_medic_start': hrapp.ex_medic_start,
                            'ex_medic_stop': hrapp.ex_medic_stop,
                            'exmedic_notas': hrapp.exmedic_notas,
                            'r_control': hrapp.r_control,
                            'r_control_start': hrapp.r_control_start,
                            'r_control_stop': hrapp.r_control_stop,
                            'r_control_gafete': hrapp.r_control_gafete,
                            'r_control_gafete_start': hrapp.r_control_gafete_start,
                            'r_control_gafete_stop': hrapp.r_control_gafete_stop,
                            'r_control_tz': hrapp.r_control_tz,
                            'no_licencia': hrapp.no_licencia,
                            'licencia_id': hrapp.licencia_id.id if hrapp.licencia_id else False,
                            'no_licencia_stop': hrapp.no_licencia_stop,
                            'no_licencia_days_to': hrapp.no_licencia_days_to,
                            'ex_medic_days_to': hrapp.ex_medic_days_to,
                            'r_control_days_to': hrapp.r_control_days_to,
                            'r_control_gafete_days_to': hrapp.r_control_gafete_days_to,
                            'comprobante_date_stop': hrapp.comprobante_date_stop,
                            'comprobante_days_to': hrapp.comprobante_days_to,

                            'ex_medic_days_to': hrapp.ex_medic_days_to,
                            'r_control_days_to': hrapp.r_control_days_to,
                            'r_control_gafete_days_to': hrapp.r_control_gafete_days_to,
                            'is_driver': hrapp.is_driver,
                          }
        res.update(data_update)
        return res

    @api.depends('comprobante_date_stop')
    def _get_days_comprobante(self):
        for rec in self:
            if not rec.comprobante_date_stop:
                rec.comprobante_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.comprobante_date_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.comprobante_days_to = total_days
                

    is_driver = fields.Boolean('Es un Operador')

    ### Campos Nuevos ###
    # ** Examen Medico ** #
    no_ex_medico = fields.Char('No. de Expediente', size=128)
    aptitud_id = fields.Many2one('hr.employee.aptitud', 'Aptitud')
    ex_medic_start = fields.Date('Inicio de vigencia')
    ex_medic_stop = fields.Date('Fin de vigencia')
    exmedic_notas = fields.Text('Notas Medicas')

    ex_medic_days_to = fields.Integer('E.M. Dias x V.', compute="_get_days_ex_medic", help='Dias por vencer', )


    # ** Aduana ** #
    r_control = fields.Char('R. Control', size=128)
    r_control_start = fields.Date('R. Control inicio')
    r_control_stop = fields.Date('R. Control final')

    r_control_days_to = fields.Integer('R.C. Dias x V.', compute="_get_days_r_control", help='Dias por vencer', )

    r_control_gafete = fields.Char('Gafete unico', size=128)
    r_control_gafete_start = fields.Date('Gafete unico inicio')
    r_control_gafete_stop = fields.Date('Gafete unico final')

    r_control_gafete_days_to = fields.Integer('G.U. Dias x V.', compute="_get_days_r_control_gafete", help='Dias por vencer', )

    r_control_tz = fields.Selection(_tz_get, string='Zona Horaria', default=lambda self: self._context.get('tz'))

    # ** Licencia ** #
    no_licencia = fields.Char('No. de Licencia', size=128)
    licencia_id = fields.Many2one('hr.employee.tipo.licencia', 'Tipo de licencia')
    no_licencia_stop = fields.Date('Vigencia de Licencia')
    no_licencia_days_to = fields.Integer('Dias por vencer', compute="_get_days")


    # ** Comprobante de Domicilio ** #
    comprobante_date_stop = fields.Date('Vigencia de Comprobante Dom.')
    comprobante_days_to = fields.Integer('Dias por vencer', compute="_get_days_comprobante")


    def create_employee(self):
        hr_app_obj = self.env['hr.applicant']
        result = {}
        context = self._context

        for hrapp in hr_app_obj.browse(context.get('active_ids')):
            hr_data_update = {
                            'no_ex_medico': self.no_ex_medico,
                            'aptitud_id': self.aptitud_id.id if self.aptitud_id else False,
                            'ex_medic_start': self.ex_medic_start,
                            'ex_medic_stop': self.ex_medic_stop,
                            'exmedic_notas': self.exmedic_notas,
                            'r_control': self.r_control,
                            'r_control_start': self.r_control_start,
                            'r_control_stop': self.r_control_stop,
                            'r_control_gafete': self.r_control_gafete,
                            'r_control_gafete_start': self.r_control_gafete_start,
                            'r_control_gafete_stop': self.r_control_gafete_stop,
                            'r_control_tz': self.r_control_tz,
                            'no_licencia': self.no_licencia,
                            'licencia_id': self.licencia_id.id if self.licencia_id else False,
                            'no_licencia_stop': self.no_licencia_stop,
                            'no_licencia_days_to': self.no_licencia_days_to,
                            'ex_medic_days_to': self.ex_medic_days_to,
                            'r_control_days_to': self.r_control_days_to,
                            'r_control_gafete_days_to': self.r_control_gafete_days_to,
                            'comprobante_date_stop': self.comprobante_date_stop,
                            'comprobante_days_to': self.comprobante_days_to,
                            
                            'is_driver': self.is_driver,
                          }
            hrapp.write(hr_data_update)

            # if self.is_driver:
            #     return hrapp.create_employee_from_applicant_data_replicant()
            # result = hrapp.create_employee_from_applicant()

            result = hrapp.create_employee_from_applicant_data_replicant()

        return result


class Applicant(models.Model):
    _name = 'hr.applicant'
    _inherit ='hr.applicant'

    @api.depends('no_licencia_stop')
    def _get_days(self):
        for rec in self:
            if not rec.no_licencia_stop:
                rec.no_licencia_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.no_licencia_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.no_licencia_days_to = total_days if total_days > 0 else 0


    @api.depends('ex_medic_stop')
    def _get_days_ex_medic(self):
        for rec in self:
            if not rec.ex_medic_stop:
                rec.ex_medic_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.ex_medic_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.ex_medic_days_to = total_days if total_days > 0 else 0

    @api.depends('r_control_stop')
    def _get_days_r_control(self):
        for rec in self:
            if not rec.r_control_stop:
                rec.r_control_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_days_to = total_days if total_days > 0 else 0


    @api.depends('r_control_gafete_stop')
    def _get_days_r_control_gafete(self):
        for rec in self:
            if not rec.r_control_gafete_stop:
                rec.r_control_gafete_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_gafete_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_gafete_days_to = total_days

    @api.depends('comprobante_date_stop')
    def _get_days_comprobante(self):
        for rec in self:
            if not rec.comprobante_date_stop:
                rec.comprobante_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.comprobante_date_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.comprobante_days_to = total_days

    is_driver = fields.Boolean('Es un Operador')

    ### Campos Nuevos ###
    # ** Examen Medico ** #
    no_ex_medico = fields.Char('No. de Expediente', size=128)
    aptitud_id = fields.Many2one('hr.employee.aptitud', 'Aptitud')
    ex_medic_start = fields.Date('Inicio de vigencia')
    ex_medic_stop = fields.Date('Fin de vigencia')
    exmedic_notas = fields.Text('Notas Medicas')

    # ** Aduana ** #
    r_control = fields.Char('R. Control', size=128)
    r_control_start = fields.Date('R. Control inicio')
    r_control_stop = fields.Date('R. Control final')
    r_control_gafete = fields.Char('Gafete unico', size=128)
    r_control_gafete_start = fields.Date('Gafete unico inicio')
    r_control_gafete_stop = fields.Date('Gafete unico final')

    r_control_tz = fields.Selection(_tz_get, string='Zona Horaria', default=lambda self: self._context.get('tz'))

    ex_medic_days_to = fields.Integer('E.M. Dias x V.', compute="_get_days_ex_medic", help='Dias por vencer', )
    r_control_days_to = fields.Integer('R.C. Dias x V.', compute="_get_days_r_control", help='Dias por vencer', )
    r_control_gafete_days_to = fields.Integer('G.U. Dias x V.', compute="_get_days_r_control_gafete", help='Dias por vencer', )


    # ** Licencia ** #
    no_licencia = fields.Char('No. de Licencia', size=128)
    licencia_id = fields.Many2one('hr.employee.tipo.licencia', 'Tipo de licencia')
    no_licencia_stop = fields.Date('Vigencia de Licencia')
    no_licencia_days_to = fields.Integer('Dias por vencer', compute="_get_days")

    # ** Comprobante de Domicilio ** #
    comprobante_date_stop = fields.Date('Vigencia de Comprobante Dom.')
    comprobante_days_to = fields.Integer('Dias por vencer', compute="_get_days_comprobante")

    ### Filtros y Documentos ###
    # ** Documentos ** #
    solicitud_empleo = fields.Binary('Solicitud de Empleo')
    solicitud_empleo_fname = fields.Char('Nombre Archivo')

    carta_recomendacion_1 = fields.Binary('Carta de Recomendación 1')
    carta_recomendacion_1_fname = fields.Char('Nombre Archivo')

    carta_recomendacion_2 = fields.Binary('Carta de Recomendación 2')
    carta_recomendacion_2_fname = fields.Char('Nombre Archivo')

    ife_ine = fields.Binary('IFE/INE')
    ife_ine_fname = fields.Char('Nombre Archivo')

    licencia_binary = fields.Binary('Licencia')
    licencia_binary_fname = fields.Char('Nombre Archivo')

    atp_medico_binary = fields.Binary('Apto Medico')
    atp_medico_binary_fname = fields.Char('Nombre Archivo')

    socioeconomico = fields.Binary('Socioeconómico')
    socioeconomico_fname = fields.Char('Nombre Archivo')

    comprobante_dom = fields.Binary('Comprobante Domicilio')
    comprobante_dom_fname = fields.Char('Nombre Archivo')

    # ** Filtros ** #
    entrevista_date = fields.Date('Entrevista')
    entrevista_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    prueba_knw_date = fields.Date('Prueba de conocimiento')
    prueba_knw_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    referencias_laborales_date = fields.Date(' Referencias laborales')
    referencias_laborales_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    psicometrico_date = fields.Date('Psicométrico')
    psicometrico_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    poligrafo_date = fields.Date('Polígrafo')
    poligrafo_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    antidoping_date = fields.Date('Antidoping')
    antidoping_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    socioeconomico_date = fields.Date('Socioeconómico')
    socioeconomico_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")


    @api.multi
    def create_employee_from_applicant_data_replicant(self):
        """ Create an hr.employee from the hr.applicants """
        employee = False
        for applicant in self:
            contact_name = False
            if applicant.partner_id:
                address_id = applicant.partner_id.address_get(['contact'])['contact']
                contact_name = applicant.partner_id.name_get()[0][1]
            else :
                new_partner_id = self.env['res.partner'].create({
                    'is_company': False,
                    'name': applicant.partner_name,
                    'email': applicant.email_from,
                    'phone': applicant.partner_phone,
                    'mobile': applicant.partner_mobile
                })
                address_id = new_partner_id.address_get(['contact'])['contact']
            if applicant.job_id and (applicant.partner_name or contact_name):
                applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
                employee = self.env['hr.employee'].create({
                    'name': applicant.partner_name or contact_name,
                    'job_id': applicant.job_id.id,
                    'address_home_id': address_id,
                    'department_id': applicant.department_id.id or False,
                    'address_id': applicant.company_id and applicant.company_id.partner_id
                            and applicant.company_id.partner_id.id or False,
                    'work_email': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.email or False,
                    'work_phone': applicant.department_id and applicant.department_id.company_id
                            and applicant.department_id.company_id.phone or False})
                applicant.write({'emp_id': employee.id})
                ### Actualización de la Información ####
                employee_data_update = {
                            'no_ex_medico': applicant.no_ex_medico,
                            'aptitud_id': applicant.aptitud_id.id if applicant.aptitud_id else False,
                            'ex_medic_start': applicant.ex_medic_start,
                            'ex_medic_stop': applicant.ex_medic_stop,
                            'exmedic_notas': applicant.exmedic_notas,
                            'r_control': applicant.r_control,
                            'r_control_start': applicant.r_control_start,
                            'r_control_stop': applicant.r_control_stop,
                            'r_control_gafete': applicant.r_control_gafete,
                            'r_control_gafete_start': applicant.r_control_gafete_start,
                            'r_control_gafete_stop': applicant.r_control_gafete_stop,
                            'r_control_tz': applicant.r_control_tz,
                            'no_licencia': applicant.no_licencia,
                            'licencia_id': applicant.licencia_id.id if applicant.licencia_id else False,
                            'no_licencia_stop': applicant.no_licencia_stop,
                            'no_licencia_days_to': applicant.no_licencia_days_to,
                            'ex_medic_days_to': applicant.ex_medic_days_to,
                            'r_control_days_to': applicant.r_control_days_to,
                            'r_control_gafete_days_to': applicant.r_control_gafete_days_to,

                            'comprobante_date_stop': applicant.comprobante_date_stop,
                            'comprobante_days_to': applicant.comprobante_days_to,
                            
                            'x_comprobante_date_stop': applicant.comprobante_date_stop,
                            'x_comprobante_days_to': applicant.comprobante_days_to,

                            'x_aduana_control_inicio': applicant.r_control_start,
                            'x_aduana_control_fin': applicant.r_control_stop,
                            'x_aduana_gafete_inicio': applicant.r_control_gafete_start,
                            'x_aduana_gafete_fin': applicant.r_control_gafete_stop,

                            'is_driver': applicant.is_driver,
                            'x_exmedic': applicant.no_ex_medico,

                            'x_exmedic_aptitud': 1 if applicant.aptitud_id else 0,
                            'x_exmedic_start': applicant.ex_medic_start,
                            'x_exmedic_end': applicant.ex_medic_stop,
                            'x_exmedic_notas': applicant.exmedic_notas,
                            
                            'x_aduana_control': applicant.r_control,
                            'x_aduana_gafete': applicant.r_control_gafete,

                            'tms_driver_license_id': applicant.no_licencia,
                            'tms_driver_license_type': applicant.licencia_id.name if applicant.licencia_id else '',
                            'tms_driver_license_expiration': applicant.no_licencia_stop,
                            'tms_driver_license_days_to_expire': applicant.no_licencia_days_to,

                          }
                employee.write(employee_data_update)

                #### Filtros y Documentos #######
                filtros_data = {
                            'entrevista_date': applicant.entrevista_date,
                            'entrevista_apto': applicant.entrevista_apto,
                            'prueba_knw_date': applicant.prueba_knw_date,
                            'prueba_knw_apto': applicant.prueba_knw_apto,
                            'referencias_laborales_date': applicant.referencias_laborales_date,
                            'referencias_laborales_apto': applicant.referencias_laborales_apto,
                            'psicometrico_date': applicant.psicometrico_date,
                            'psicometrico_apto': applicant.psicometrico_apto,
                            'poligrafo_date': applicant.poligrafo_date,
                            'poligrafo_apto': applicant.poligrafo_apto,
                            'antidoping_date': applicant.antidoping_date,
                            'antidoping_apto': applicant.antidoping_apto,
                            'socioeconomico_date': applicant.socioeconomico_date,
                            'socioeconomico_apto': applicant.socioeconomico_apto,
                            
                            'x_poligrafo_date': applicant.poligrafo_date,
                            'x_poligrafo_apto': applicant.poligrafo_apto,
                            'x_antidoping_date': applicant.antidoping_date,
                            'x_antidoping_apto': applicant.antidoping_apto,
                            'x_socioeconomico_date': applicant.socioeconomico_date,
                            'x_socioeconomico_apto': applicant.socioeconomico_apto,
                            }
                employee.write(filtros_data)

                documentos_data = {
                            'solicitud_empleo': applicant.solicitud_empleo,
                            'solicitud_empleo_fname': applicant.solicitud_empleo_fname,
                            'carta_recomendacion_1': applicant.carta_recomendacion_1,
                            'carta_recomendacion_1_fname': applicant.carta_recomendacion_1_fname,
                            'carta_recomendacion_2': applicant.carta_recomendacion_2,
                            'carta_recomendacion_2_fname': applicant.carta_recomendacion_2_fname,
                            'ife_ine': applicant.ife_ine,
                            'ife_ine_fname': applicant.ife_ine_fname,
                            'licencia_binary': applicant.licencia_binary,
                            'licencia_binary_fname': applicant.licencia_binary_fname,
                            'atp_medico_binary': applicant.atp_medico_binary,
                            'atp_medico_binary_fname': applicant.atp_medico_binary_fname,
                            'socioeconomico': applicant.socioeconomico,
                            'socioeconomico_fname': applicant.socioeconomico_fname,
                            'comprobante_dom': applicant.comprobante_dom,
                            'comprobante_dom_fname': applicant.comprobante_dom_fname,

                            }
                employee.write(documentos_data)
                ##### Creando los Adjuntos ####
                ir_attachment = self.env['ir.attachment']
                if applicant.solicitud_empleo:
                    data_attach_doc = {
                            'name'        : 'Solicitud de Empleo',
                            'datas'       : applicant.solicitud_empleo,
                            'datas_fname' : applicant.solicitud_empleo_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.carta_recomendacion_1:
                    data_attach_doc = {
                            'name'        : 'Carta de Recomendación 01',
                            'datas'       : applicant.carta_recomendacion_1,
                            'datas_fname' : applicant.carta_recomendacion_1_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.carta_recomendacion_2:
                    data_attach_doc = {
                            'name'        : 'Carta de Recomendación 02',
                            'datas'       : applicant.carta_recomendacion_2,
                            'datas_fname' : applicant.carta_recomendacion_2_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.ife_ine:
                    data_attach_doc = {
                            'name'        : 'IFE/INE',
                            'datas'       : applicant.ife_ine,
                            'datas_fname' : applicant.ife_ine_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.licencia_binary:
                    data_attach_doc = {
                            'name'        : 'Licencia',
                            'datas'       : applicant.licencia_binary,
                            'datas_fname' : applicant.licencia_binary_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.atp_medico_binary:
                    data_attach_doc = {
                            'name'        : 'Apartado Medico',
                            'datas'       : applicant.atp_medico_binary,
                            'datas_fname' : applicant.atp_medico_binary_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)
                if applicant.socioeconomico:
                    data_attach_doc = {
                            'name'        : 'Examen Socioeconómico',
                            'datas'       : applicant.socioeconomico,
                            'datas_fname' : applicant.socioeconomico_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)

                if applicant.comprobante_dom:
                    data_attach_doc = {
                            'name'        : 'Comprobante de Domicilio',
                            'datas'       : applicant.comprobante_dom,
                            'datas_fname' : applicant.comprobante_dom_fname,
                            'description' : 'Proceso de Reclutamiento: %s' % applicant.name,
                            'res_model'   : 'hr.employee',
                            'res_id'      : employee.id,
                            'type'        : 'binary',
                        }
                    attachment_id = ir_attachment.create(data_attach_doc)

                applicant.job_id.message_post(
                    body='Nuevo Empleado %s Contratado' % applicant.partner_name if applicant.partner_name else applicant.name,
                    subtype="hr_recruitment.mt_job_applicant_hired")
            else:
                raise UserError(_('.'))

        employee_action = self.env.ref('hr.open_view_employee_list')
        dict_act_window = employee_action.read([])[0]
        dict_act_window['context'] = {'form_view_initial_mode': 'edit'}
        dict_act_window['res_id'] = employee.id
        return dict_act_window

class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit ='hr.employee'

    @api.depends('no_licencia_stop')
    def _get_days(self):
        for rec in self:
            if not rec.no_licencia_stop:
                rec.no_licencia_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.no_licencia_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.no_licencia_days_to = total_days if total_days > 0 else 0


    @api.depends('ex_medic_stop')
    def _get_days_ex_medic(self):
        for rec in self:
            if not rec.ex_medic_stop:
                rec.ex_medic_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.ex_medic_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.ex_medic_days_to = total_days if total_days > 0 else 0

    @api.depends('r_control_stop')
    def _get_days_r_control(self):
        for rec in self:
            if not rec.r_control_stop:
                rec.r_control_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_days_to = total_days if total_days > 0 else 0


    @api.depends('r_control_gafete_stop')
    def _get_days_r_control_gafete(self):
        for rec in self:
            if not rec.r_control_gafete_stop:
                rec.r_control_gafete_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.r_control_gafete_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.r_control_gafete_days_to = total_days if total_days > 0 else 0

    #### Campos Extras #####
    
    @api.depends('x_exmedic_end')
    def _get_days_ex_medic_x_fields(self):
        for rec in self:
            if not rec.x_exmedic_end:
                rec.x_ex_medic_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.x_exmedic_end)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.x_ex_medic_days_to = total_days if total_days > 0 else 0

    @api.depends('x_aduana_control_fin')
    def _get_days_r_control_x_fields(self):
        for rec in self:
            if not rec.x_aduana_control_fin:
                rec.x_r_control_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.x_aduana_control_fin)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.x_r_control_days_to = total_days if total_days > 0 else 0


    @api.depends('x_aduana_gafete_fin')
    def _get_days_r_control_gafete_x_fields(self):
        for rec in self:
            if not rec.x_aduana_gafete_fin:
                rec.x_r_control_gafete_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.x_aduana_gafete_fin)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.x_r_control_gafete_days_to = total_days if total_days > 0 else 0

    @api.depends('comprobante_date_stop')
    def _get_days_comprobante(self):
        for rec in self:
            if not rec.comprobante_date_stop:
                rec.comprobante_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.comprobante_date_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.comprobante_days_to = total_days

    @api.depends('x_comprobante_date_stop')
    def _get_days_comprobante(self):
        for rec in self:
            if not rec.x_comprobante_date_stop:
                rec.x_comprobante_days_to = 0
            else:
                start_date_dt = fields.Date.context_today(self)
                end_date_dt = fields.Date.from_string(rec.x_comprobante_date_stop)
                # Here, we compute the amount of the cutoff
                # That's the important part !
                total_days = (end_date_dt - start_date_dt).days

                rec.x_comprobante_days_to = total_days

    # ** Comprobante de Domicilio ** #
    x_comprobante_date_stop = fields.Date('Vigencia de Comprobante Dom.')
    x_comprobante_days_to = fields.Integer('Dias por vencer', compute="_get_days_comprobante")

    is_driver = fields.Boolean('Es un Operador')
    x_exmedic = fields.Char('No. de Expediente', size=128)

    x_exmedic_aptitud = fields.Selection([(1,'SI'),(0,'NO')], string="Aptitud")
    x_exmedic_start = fields.Date('Inicio de vigencia')
    x_exmedic_end = fields.Date('Fin de vigencia')
    x_exmedic_notas = fields.Text('Notas Medicas')

    x_poligrafo_date = fields.Date('Polígrafo')
    x_poligrafo_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    x_antidoping_date = fields.Date('Antidoping')
    x_antidoping_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    x_socioeconomico_date = fields.Date('Socioeconómico')
    x_socioeconomico_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    x_aduana_control = fields.Char('R. Control', size=128)
    x_aduana_gafete = fields.Char('Gafete único', size=128)

    x_aduana_control_inicio = fields.Date('R.C. Inicio')
    x_aduana_control_fin = fields.Date('R.C. Final')
    x_aduana_gafete_inicio = fields.Date('G.U. Inicio')
    x_aduana_gafete_fin = fields.Date('G.U. Final')

    x_ex_medic_days_to = fields.Integer('E.M. Dias x V.', compute="_get_days_ex_medic_x_fields", help='Dias por Vencer', )
    x_r_control_days_to = fields.Integer('R.C. Dias x V.', compute="_get_days_r_control_x_fields", help='Dias por Vencer', )
    x_r_control_gafete_days_to = fields.Integer('G.U. Dias x V.', compute="_get_days_r_control_gafete_x_fields", help='Dias por Vencer', )


    ### Campos Nuevos ###
    # ** Examen Medico ** #
    no_ex_medico = fields.Char('No. de Expediente', size=128)
    aptitud_id = fields.Many2one('hr.employee.aptitud', 'Aptitud')
    ex_medic_start = fields.Date('Inicio de vigencia')
    ex_medic_stop = fields.Date('Fin de vigencia')
    exmedic_notas = fields.Text('Notas Medicas')

    # ** Aduana ** #
    r_control = fields.Char('R. Control', size=128)
    r_control_start = fields.Date('R. Control inicio')
    r_control_stop = fields.Date('R. Control final')
    r_control_gafete = fields.Char('Gafete unico', size=128)
    r_control_gafete_start = fields.Date('Gafete unico inicio')
    r_control_gafete_stop = fields.Date('Gafete unico final')

    r_control_tz = fields.Selection(_tz_get, string='Zona Horaria', default=lambda self: self._context.get('tz'))

    ex_medic_days_to = fields.Integer('E.M. Dias x V.', compute="_get_days_ex_medic", help='Dias por vencer', )
    r_control_days_to = fields.Integer('R.C. Dias x V.', compute="_get_days_r_control", help='Dias por vencer', )
    r_control_gafete_days_to = fields.Integer('G.U. Dias x V.', compute="_get_days_r_control_gafete", help='Dias por vencer', )


    # ** Licencia ** #
    no_licencia = fields.Char('No. de Licencia', size=128)
    licencia_id = fields.Many2one('hr.employee.tipo.licencia', 'Tipo de licencia')
    no_licencia_stop = fields.Date('Vigencia de Licencia')
    no_licencia_days_to = fields.Integer('Dias por vencer', compute="_get_days")


    # ** Comprobante de Domicilio ** #
    comprobante_date_stop = fields.Date('Vigencia de Comprobante Dom.')
    comprobante_days_to = fields.Integer('Dias por vencer', compute="_get_days_comprobante")


    ### Filtros y Documentos ###

    entrevista_date = fields.Date('Entrevista')
    entrevista_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    prueba_knw_date = fields.Date('Prueba de conocimiento')
    prueba_knw_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    referencias_laborales_date = fields.Date(' Referencias laborales')
    referencias_laborales_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    psicometrico_date = fields.Date('Psicométrico')
    psicometrico_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    poligrafo_date = fields.Date('Polígrafo')
    poligrafo_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    antidoping_date = fields.Date('Antidoping')
    antidoping_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")

    socioeconomico_date = fields.Date('Socioeconómico')
    socioeconomico_apto = fields.Selection([('Apto','Apto'),('NO','NO')], string="Apto")


    ### Filtros y Documentos ###
    # ** Documentos ** #
    solicitud_empleo = fields.Binary('Solicitud de Empleo')
    solicitud_empleo_fname = fields.Char('Nombre Archivo')

    carta_recomendacion_1 = fields.Binary('Carta de Recomendación 1')
    carta_recomendacion_1_fname = fields.Char('Nombre Archivo')

    carta_recomendacion_2 = fields.Binary('Carta de Recomendación 2')
    carta_recomendacion_2_fname = fields.Char('Nombre Archivo')

    ife_ine = fields.Binary('IFE/INE')
    ife_ine_fname = fields.Char('Nombre Archivo')

    licencia_binary = fields.Binary('Licencia')
    licencia_binary_fname = fields.Char('Nombre Archivo')

    atp_medico_binary = fields.Binary('Apto Medico')
    atp_medico_binary_fname = fields.Char('Nombre Archivo')

    socioeconomico = fields.Binary('Socioeconómico')
    socioeconomico_fname = fields.Char('Nombre Archivo')

    comprobante_dom = fields.Binary('Comprobante Domicilio')
    comprobante_dom_fname = fields.Char('Nombre Archivo')

    # ** Filtros ** #
    entrevista_date = fields.Date('Entrevista')
    entrevista_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    prueba_knw_date = fields.Date('Prueba de conocimiento')
    prueba_knw_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    referencias_laborales_date = fields.Date(' Referencias laborales')
    referencias_laborales_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    psicometrico_date = fields.Date('Psicométrico')
    psicometrico_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    poligrafo_date = fields.Date('Polígrafo')
    poligrafo_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    antidoping_date = fields.Date('Antidoping')
    antidoping_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

    socioeconomico_date = fields.Date('Socioeconómico')
    socioeconomico_apto = fields.Selection([('APTO','APTO'),('NO','NO')], string="Apto")

