# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"    

    @api.multi
    def _prepare_invoice(self):        
        res = super(SaleOrder, self)._prepare_invoice()
        res.update({'addenda_mandatory' : self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_invoice_mandatory) or self.partner_id.addenda_invoice_mandatory) or False,
                    'addenda_manual' : self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_invoice_manual) or self.partner_id.addenda_invoice_manual) or False,
                    'addenda_jinja' : self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_invoice_jinja) or self.partner_id.addenda_invoice_jinja) or False,
                    'addenda' : self.partner_id and ((self.partner_id.parent_id and self.partner_id.parent_id.addenda_invoice) or self.partner_id.addenda_invoice) or False,
        })
        return res     

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    