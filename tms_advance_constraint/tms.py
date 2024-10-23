# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import api, models, fields
from odoo.exceptions import UserError, RedirectWarning, ValidationError


class tms_advance(models.Model):
    _name = 'tms.advance'
    _inherit ='tms.advance'


    @api.model
    def create(self, vals):
        #print "vals: ", vals
        res = super(tms_advance, self).create(vals)
        if res.travel_id and res.travel_id.state == 'closed':
        	raise ValidationError("No se pueden crear Anticipos en Viajes Cerrados.")

        return res

    @api.multi    
    def action_approve(self):
        res = super(tms_advance, self).action_approve()
        for rec in self:
            if rec.travel_id.state == 'closed':
                raise ValidationError("No se puede aprobar el Anticipo ya que el viaje se encuentra Cerrado")
        return res

class tms_fuelvoucher(models.Model):
    _name = 'tms.fuelvoucher'
    _inherit ='tms.fuelvoucher'


    @api.model
    def create(self, vals):
        #print "vals: ", vals
        res = super(tms_fuelvoucher, self).create(vals)
        if res.travel_id and res.travel_id.state == 'closed':
                raise ValidationError("No se pueden crear Vales en Viajes Cerrados.")

        return res

    @api.multi    
    def action_approve(self):
        res = super(tms_fuelvoucher, self).action_approve()
        for rec in self:
            if rec.travel_id.state == 'closed':
                raise ValidationError("No se puede aprobar el Vale ya que el viaje se encuentra Cerrado")
        return res

