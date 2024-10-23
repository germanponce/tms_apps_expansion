# -*- encoding: utf-8 -*-   

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError
import xml
import sys
import base64
import jinja2
import logging
_logger = logging.getLogger(__name__)
    
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    addenda_template = fields.Selection([('none','Sin Plantilla')], string="Plantilla Addenda", copy=False, default='none', readonly=True, related="partner_id.addenda_template")
    #####################################
    name = fields.Char(string='Reference/Description', index=True,
        readonly=True, states={'draft': [('readonly', False)], 'open': [('readonly', False)]}, copy=False, help='The name that will be used on account move lines')
    
    addenda_mandatory = fields.Boolean('Requiere Addenda', readonly=True, states={'draft': [('readonly', False)]})
    addenda_ok = fields.Boolean('Addenda Ok', readonly=True, help="Addenda Generada exitosamente", copy=False)
    addenda_manual = fields.Boolean('Insertar Addenda Post-Timbrado', readonly=True, states={'draft': [('readonly', False)]},
                                    help="La Addenda no se creará ANTES de enviar el correo al cliente, o sea, no se generará de manera automática ni se insertará en el archivo XML timbrado sino por la acción manual del usuario")
    addenda_jinja = fields.Boolean('Addenda en XML', readonly=True, states={'draft': [('readonly', False)]},
                                  help="Indica si la Addenda deberá ser definida como XML a insertarse en el XML del CFDI (en algunos casos la Addenda no se agrega como XML dentro del CFDI)")
    addenda = fields.Text(string='Addenda', readonly=True, states={'draft': [('readonly', False)]})
    addenda_computed = fields.Text(string='Addenda Calculada', readonly=True, 
                                   states={'draft': [('readonly', False)]},
                                   help="Este campo será usado para ser insertado como Addenda",  copy=False)
    #####################################
    
    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        
        self.addenda_mandatory = self.partner_id and ((self.partner_id.commercial_partner_id and \
                                                       self.partner_id.commercial_partner_id.addenda_invoice_mandatory) or \
                                                      self.partner_id.addenda_invoice_mandatory) or False
        
        self.addenda_jinja = self.partner_id and ((self.partner_id.commercial_partner_id and \
                                                   self.partner_id.commercial_partner_id.addenda_invoice_jinja) or \
                                                  self.partner_id.addenda_invoice_jinja) or False
        
        self.addenda = self.partner_id and ((self.partner_id.commercial_partner_id and \
                                             self.partner_id.commercial_partner_id.addenda_invoice) or self.partner_id.addenda_invoice) or False
        return res

    
    def compute_addenda(self):
        try:
            tmpl = jinja2.Template(self.addenda)
            dictargs = {'o': self}
            addenda = tmpl.render(**dictargs)
            self.addenda_computed = addenda
            return True
        except:
            raise UserError(_("Error en definición de Addenda !\n\n%s") % sys.exc_info()[0])
            return False
    
    
    @api.multi
    def do_something_with_xml_attachment(self, attach):
        self.ensure_one()
        res = super(AccountInvoice, self).do_something_with_xml_attachment(attach)
        if self.type not in ('out_invoice','out_refund') or self.addenda_manual or not self.addenda_mandatory:
            return res
        if self.addenda_jinja and not self.addenda_computed:
            addenda = False
            try:
                tmpl = jinja2.Template(self.addenda)
                dictargs = {'o': self}
                addenda = tmpl.render(**dictargs)
            except:
                raise UserError(_("Error en definición de Addenda !\n\n%s") % sys.exc_info()[0])
                _logger.error('Advertencia !!! Ocurrió un error al generar la Addenda !!!')            
        else:
            addenda = self.addenda_computed or self.addenda
        if not addenda:
            return res
        addenda = addenda.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '').replace('<?xml version="1.0" encoding="UTF-8"?>','')
        addenda = str.encode(addenda)
        xml_data = base64.b64decode(attach.datas)        
        xml_data = xml_data.replace(b'</cfdi:Comprobante>', b'\n' + addenda + b'\n</cfdi:Comprobante>')
        attach.write({'datas' : base64.encodestring(xml_data)})
        self.write({'xml_file_signed_index' : xml_data,
                    'addenda_ok'        :True,
                    'addenda_manual'    :False,
                    'addenda_computed'  : addenda,})
        return res
        
        
class AccountInvoiceAddenda(models.TransientModel):
    _name = 'account.invoice.addenda.wizard'
    _description = 'Wizard para generar la Addenda e insertarla en el CFDI Timbrado'
    
    state           = fields.Selection([('step1','Por Generar'),
                                        ('step2','Generada'),
                                        ('step3','Insertar en XML de Factura'),
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
    invoice_id      = fields.Many2one('account.invoice',string="Factura", readonly=True)

    
    @api.model	
    def default_get(self, fields):
        res = super(AccountInvoiceAddenda, self).default_get(fields)
        ids = self._context.get('active_ids', [])
        if not len(ids) == 1:
            raise UserError(_('Advertencia !!! No ha seleccionado ninguna factura o seleccionó mas de una factura...'))
        
        invoice = self.env['account.invoice'].browse(ids)
        res.update({'addenda_jinja' : invoice.addenda_jinja,
                    'addenda'       : invoice.addenda,
                    'invoice_id'    : invoice.id,
                   })
        
        return res    
    
    
    @api.multi
    def _reopen_wizard(self):
        return { 'type'     : 'ir.actions.act_window',
                 'res_id'   : self.id,
                 'view_mode': 'form',
                 'view_type': 'form',
                 'res_model': 'account.invoice.addenda.wizard',
                 'target'   : 'new',
                 'name'     : 'Addenda'}
    
    
    @api.multi
    def step1_create_addenda(self):
        if self.addenda_jinja and self.addenda:
            self.invoice_id.write({'addenda_jinja' : self.addenda_jinja, 'addenda' : self.addenda})
            res = self.invoice_id.compute_addenda()
            if res:
                self.write({'addenda_computed' : self.invoice_id.addenda_computed,
                            'state' : 'step2'})
            else:
                self.write({'error_log' : 'Error !!! No se pudo generar la Addenda, revise la definición e intente nuevamente...',
                            'state' : 'error'})
        elif not self.addenda_jinja and self.addenda:
            self.invoice_id.addenda_computed = self.addenda
            self.addenda_computed = self.addenda
            self.state = 'step2'            
        return self._reopen_wizard()

    
    @api.multi
    def step2_insert_addenda(self):        
        if not self.invoice_id.compute_addenda():
            self.write({'error_log' : 'Error !!! No se generó ninguna Addenda, revise la definición e intente nuevamente...',
                            'state' : 'step1'})
        else:
            self.invoice_id.addenda_computed = self.addenda_computed
            addenda = self.invoice_id.addenda_computed.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '').replace('<?xml version="1.0" encoding="UTF-8"?>','')
            addenda = str.encode(addenda)
            attach = False
            for rec in self.env['ir.attachment'].search([('res_model', '=', 'account.invoice'), ('res_id', '=', self.invoice_id.id)]):
                if rec.name.endswith('.xml'):
                    attach = rec
            
            xml_data = base64.b64decode(attach.datas)
            xml_data = xml_data.replace(b'</cfdi:Comprobante>', b'\n' + addenda + b'\n</cfdi:Comprobante>')
            attach.write({'datas' : base64.encodestring(xml_data)})
            self.invoice_id.write({'xml_file_signed_index' : xml_data,
                                   'addenda_ok':True,
                                   'addenda_manual':False})
            self.state = 'step3'
            
        return self._reopen_wizard()            
        
        
    @api.multi
    def step3_enviar_factura(self):
        self.state = 'step4'
        return self.invoice_id.action_invoice_sent()


    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: