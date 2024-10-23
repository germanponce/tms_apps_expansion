# -*- encoding: utf-8 -*-   
#import sys
#reload(sys)
#sys.setdefaultencoding('utf-8')
from openerp import api, fields, models, _, tools, release  
from openerp.exceptions import UserError
import xml
import base64
import jinja2
import logging
_logger = logging.getLogger(__name__)



class AccountPaymentWizard(models.TransientModel):
    _inherit = "account.register.payments"
    
    addenda_mandatory = fields.Boolean('Addenda Obligatoria')
    addenda_manual = fields.Boolean('Addenda Manual Post-Timbrado',
                                    help="La Addenda no se creará ANTES de enviar el correo al cliente, o sea, no se generará de manera automática ni se insertará en el archivo XML timbrado sino por la acción manual del usuario")
    addenda_jinja = fields.Boolean('Addenda en Jinja')
    addenda = fields.Text(string='Addenda Factura')
    addenda_ok = fields.Boolean('Addenda Ok', readonly=True, help="Addenda Generada exitosamente", copy=False)
    
    @api.model
    def default_get(self, fields):
        rec = super(AccountPaymentWizard, self).default_get(fields)
        if 'payment_type' in rec and rec['payment_type']=='inbound' and 'partner_id' in rec:
            partner = self.env['res.partner'].browse(rec['partner_id'])
            rec['addenda_mandatory'] = (partner.parent_id and partner.parent_id.addenda_payment_mandatory) or \
                                        partner.addenda_payment_mandatory
            rec['addenda_jinja']     = (partner.parent_id and partner.parent_id.addenda_payment_jinja) or \
                                        partner.addenda_payment_jinja
            rec['addenda']           = (partner.parent_id and partner.parent_id.addenda_payment) or \
                                        partner.addenda_payment
        return rec
    
    
    def get_payment_vals(self):
        res = super(AccountPaymentWizard, self).get_payment_vals()
        res.update({'addenda_mandatory' : self.partner_id and ((self.partner_id.parent_id and \
                                                                self.partner_id.parent_id.addenda_payment_mandatory) or \
                                                                self.partner_id.addenda_payment_mandatory) or False,
                    'addenda_jinja'     : self.partner_id and ((self.partner_id.parent_id and \
                                                                self.partner_id.parent_id.addenda_payment_jinja) or \
                                                                self.partner_id.addenda_payment_jinja) or False,
                    'addenda'           : self.partner_id and ((self.partner_id.parent_id and \
                                                                self.partner_id.parent_id.addenda_payment) or \
                                                               self.partner_id.addenda_payment) or False,
            })
        return res



class AccountPayment(models.Model):
    _inherit = 'account.payment'

    #####################################
    addenda_mandatory = fields.Boolean('Addenda Obligatoria', readonly=True, states={'draft': [('readonly', False)]})
    addenda_ok = fields.Boolean('Addenda Ok', readonly=True, help="Addenda Generada exitosamente", copy=False)
    addenda_manual = fields.Boolean('Addenda Manual Post-Timbrado', readonly=True, states={'draft': [('readonly', False)]},
                                    help="La Addenda no se creará ANTES de enviar el correo al cliente, o sea, no se generará de manera automática ni se insertará en el archivo XML timbrado sino por la acción manual del usuario")
    addenda_jinja = fields.Boolean('Addenda en Jinja', readonly=True, states={'draft': [('readonly', False)]})
    addenda = fields.Text(string='Addenda Factura', readonly=True, states={'draft': [('readonly', False)]})
    addenda_computed = fields.Text(string='Addenda Calculada', help="Este campo será usado para ser insertado como Addenda", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    #####################################
    
    
    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        if 'payment_type' in rec and rec['payment_type']=='inbound' and 'partner_id' in rec:
            partner = self.env['res.partner'].browse(rec['partner_id'])
            rec['addenda_mandatory'] = (partner.parent_id and partner.parent_id.addenda_payment_mandatory) or \
                                        partner.addenda_payment_mandatory
            rec['addenda_jinja']     = (partner.parent_id and partner.parent_id.addenda_payment_jinja) or \
                                        partner.addenda_payment_jinja
            rec['addenda']           = (partner.parent_id and partner.parent_id.addenda_payment) or \
                                        partner.addenda_payment
        return rec
    
    #if release.major_version == "9.0":
    #    @api.onchange('partner_id')
    #    def _onchange_partner_id(self):
    #        self.addenda_mandatory = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment_mandatory) or self.partner_id.addenda_payment_mandatory) or False

    #        self.addenda_jinja = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment_jinja) or self.partner_id.addenda_payment_jinja) or False

     #       self.addenda = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment) or self.partner_id.addenda_payment) or False
        
    if release.major_version == "10.0":
        @api.onchange('partner_id', 'company_id')
        def _onchange_partner_id(self):
            res = super(AccountPayment, self)._onchange_partner_id()

            self.addenda_mandatory = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment_mandatory) or self.partner_id.addenda_payment_mandatory) or False

            self.addenda_jinja = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment_jinja) or self.partner_id.addenda_payment_jinja) or False

            self.addenda = self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_payment) or self.partner_id.addenda_payment) or False

    
    @api.one
    def compute_addenda(self):
        try:
            tmpl = jinja2.Template(self.addenda)
            dictargs = {'o': self}
            addenda = tmpl.render(**dictargs)
            self.addenda_computed = addenda
            return True
        except:
            return False
    
    
    @api.multi
    def do_something_with_xml_attachment(self, attach):
        self.ensure_one()
        res = super(AccountPayment, self).do_something_with_xml_attachment(attach)
        if self.payment_type != 'inbound' or self.addenda_manual or not self.addenda_mandatory:
            return res
        if self.addenda_jinja and not self.addenda_computed:
            addenda = False
            try:
                tmpl = jinja2.Template(self.addenda)
                dictargs = {'o': self}
                addenda = tmpl.render(**dictargs)
            except:
                _logger.error('Advertencia !!! Ocurrió un error al generar la Addenda !!!')            
        else:
            addenda = self.addenda_computed or self.addenda
        if not addenda:
            return res
        addenda = addenda.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '').replace('<?xml version="1.0" encoding="UTF-8"?>','')
        xml_data = base64.b64decode(attach.datas)
        xml_data = xml_data.replace('</cfdi:Comprobante>', '\n' + addenda + '\n</cfdi:Comprobante>')
        attach.write({'datas' : base64.encodestring(xml_data.encode('utf8'))})
        self.write({'xml_file_signed_index' : xml_data.encode('utf8'),
                   'addenda_ok':True,
                   'addenda_manual':False})
        return res
    
    @api.multi
    def action_payment_sent(self):
        """ Open a window to compose an email, with the edi invoice template
            message loaded by default
        """
        self.ensure_one()
        report_name = self.journal_id.report_id
        template = self.env['mail.template'].search([('model_id.model', '=', 'account.payment'),
                                                     #('company_id','=', self.company_id.id),
                                                     #('report_template.report_name', '=',report_name.name)
                                                    ], limit=1)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='account.payment',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode='comment',
            resend=True,
        )
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }    
        
        
class AccountPaymentAddenda(models.TransientModel):
    _name = 'account.payment.addenda.wizard'
    _description = 'Wizard para generar la Addenda e insertarla en el CFDI Timbrado'
    
    state           = fields.Selection([('step1','Por Generar'),
                                        ('step2','Generada'),
                                        ('step3','Insertar en XML de CFDI'),
                                        ('step4','Hecho'),
                                        ('error','Error al Generar Addenda'),],
                                      string="Estado", default='step1')
    addenda_jinja   = fields.Boolean('Addenda en Jinja', readonly=True, states={'step1': [('readonly', False)]})
    addenda         = fields.Text(string='Addenda Factura', readonly=True, 
                                  states={'step1': [('readonly', False)],'step2': [('readonly', False)]})
    addenda_computed= fields.Text(string='Addenda Calculada', readonly=True, 
                                  states={'step1': [('readonly', False)],'step2': [('readonly', False)]},
                                  help="Este campo será usado para ser insertado como Addenda")
    error_log       = fields.Text(string="Error", default='', readonly=True)
    payment_id      = fields.Many2one('account.payment',string="Factura", readonly=True)

    
    @api.model	
    def default_get(self, fields):
        res = super(AccountPaymentAddenda, self).default_get(fields)
        ids = self._context.get('active_ids', [])
        if not len(ids) == 1:
            raise UserError(_('Advertencia !!! No ha seleccionado ningún registro o seleccionó mas de uno...'))
        
        payment = self.env['account.payment'].browse(ids)
        res.update({'addenda_jinja' : payment.addenda_jinja,
                    'addenda'       : payment.addenda,
                    'payment_id'    : payment.id,
                   })
        
        return res    
    
    
    @api.multi
    def _reopen_wizard(self):
        return { 'type'     : 'ir.actions.act_window',
                 'res_id'   : self.id,
                 'view_mode': 'form',
                 'view_type': 'form',
                 'res_model': 'account.payment.addenda.wizard',
                 'target'   : 'new',
                 'name'     : 'Addenda'}
    
    
    @api.multi
    def step1_create_addenda(self):
        if self.addenda_jinja and self.addenda:
            self.payment_id.write({'addenda_jinja' : self.addenda_jinja, 'addenda' : self.addenda})
            if self.payment_id.compute_addenda():
                self.write({'addenda_computed' : self.payment_id.addenda_computed,
                            'state' : 'step2'})
            else:
                self.write({'error_log' : 'Error !!! No se pudo generar la Addenda, revise la definición e intente nuevamente...',
                            'state' : 'step2'})
        elif not self.addenda_jinja and self.addenda:
            self.payment_id.addenda_computed = self.addenda
            self.addenda_computed = self.addenda
            self.state = 'step2'
            
        return self._reopen_wizard()

    
    @api.multi
    def step2_insert_addenda(self):        
        if not self.payment_id.compute_addenda():
            self.write({'error_log' : 'Error !!! No se generó ninguna Addenda, revise la definición e intente nuevamente...',
                            'state' : 'step1'})
        else:
            self.payment_id.addenda_computed = self.addenda_computed
            addenda = self.payment_id.addenda_computed.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '').replace('<?xml version="1.0" encoding="UTF-8"?>','')
            addenda = str.encode(addenda)
            attach = False
            for rec in self.env['ir.attachment'].search([('res_model', '=', 'account.payment'), ('res_id', '=', self.payment_id.id)]):
                if rec.name.endswith('.xml'):
                    attach = rec
            
            xml_data = base64.b64decode(attach.datas)
            xml_data = xml_data.replace(b'</cfdi:Comprobante>', b'\n' + addenda + b'\n</cfdi:Comprobante>')
            attach.write({'datas' : base64.encodestring(xml_data)})
            self.payment_id.write({'xml_file_signed_index' : xml_data,
                                   'addenda_ok':True,
                                   'addenda_manual':False})
            self.state = 'step3'
            
        return self._reopen_wizard()            
        
        
    @api.multi
    def step3_enviar_factura(self):
        self.state = 'step4'
        return self.payment_id.action_payment_sent()



    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: