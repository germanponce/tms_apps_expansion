# -*- encoding: utf-8 -*-   
from odoo import api, fields, models, _, tools
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import xml
import jinja2
from xml.parsers.expat import ExpatError

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    @api.one
    @api.depends()
    def _get_ejemplo_addenda(self):
        self.addenda_ejemplo_jinja = """
<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Addenda>
    <NumProv>{{ o.partner_id.ref }}</NumProv>
    <OrdenCompra>{{ o.name }}</OrdenCompra>
    <Lineas>
    {% for l in o.invoice_line_ids %}
        <Linea Prod="{{ l.product_id.default_code }}" Cant="{{'{0:0.2f}'.format(l.quantity)}}" Precio="{{'{0:0.2f}'.format(l.price_unit)}}" />
    {% endfor %}
    </Lineas>
</cfdi:Addenda>
        """
        self.addenda_ejemplo = """
<?xml version="1.0" encoding="UTF-8"?>
<cfdi:Addenda>
    <NumProv>123456</NumProv>
    <OrdenCompra>OC-34598</OrdenCompra>
    <FechaOC>2017-02-27</FechaOC>
</cfdi:Addenda>
        """


    addenda_template = fields.Selection([('none','Sin Plantilla')], string="Plantilla Addenda", help='Permite generar Addendas Credas por Modulos que extiendan la funcionalidad de las Addendas.', )

    addenda_invoice_mandatory = fields.Boolean('Addenda Obligatoria')
    addenda_invoice_manual = fields.Boolean('Addenda Manual Post-Timbrado', 
                                            help="La Addenda no se creará ANTES de enviar el correo al cliente, o sea, no se generará de manera automática ni se insertará en el archivo XML timbrado sino por la acción manual del usuario")
    addenda_invoice_jinja = fields.Boolean('Addenda Dinámica')
    addenda_ejemplo_jinja = fields.Text(string="Ejemplo Addenda Jinja", compute="_get_ejemplo_addenda", store=False)
    addenda_ejemplo = fields.Text(string="Ejemplo Addenda", compute="_get_ejemplo_addenda", store=False)
    addenda_invoice = fields.Text(string='Addenda Factura', default='<?xml version="1.0" encoding="UTF-8"?>')

    
    @api.one
    def validate_addenda(self):
        tipo = self._context.get('tipo_addenda')
        if (tipo=='invoice' and not self.addenda_invoice) or (tipo=='payment' and not self.addenda_payment):
            raise ValidationError(_('Advertencia !!!\n\nLa definición de la Addenda para %s está vacía, por favor revise...') % (tipo=='invoice' and 'CFDI Factura' or 'CFDI Pagos'))
        addenda = (tipo=='invoice' and self.addenda_invoice or self.addenda_payment)
        if (tipo=='invoice' and not self.addenda_invoice_jinja) or (tipo=='payment' and not self.addenda_payment_jinja):
            try:
                if '<?xml version="1.0" encoding="UTF-8"?>' not in addenda:
                    addenda = '<?xml version="1.0" encoding="UTF-8"?>\n' + addenda                
                doc_xml = xml.dom.minidom.parseString(addenda)
            except ExpatError:
                error = str(ExpatError)
                raise ValidationError(_('Advertencia !!!\n\nLa definición de la Addenda es incorrecta y no puede procesarse para CFDI, revise el error: \n\n%s') % (e))
            raise UserError(_('La definición de la Addenda parece cumplir el estándar XML, sin embargo es necesario validarla con datos reales de un CFDI...'))
        else:
            try:
                #addenda = addenda.replace('<?xml version="1.0" encoding="UTF-8"?>\n', '').replace('\n','')
                res = jinja2.Template(addenda)
            except:
                raise ValidationError(_('Advertencia !!!\n\nLa definición de la Addenda es incorrecta y no cumple con la notación de Jinja2, por consiguiente no puede procesarse para CFDI, por favor revise...'))
            raise Warning(_('Notificación !!!\n\nLa definición de la Addenda parece cumplir con la Jinja2, sin embargo es necesario validarla con datos reales de un CFDI...'))
        return True
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: