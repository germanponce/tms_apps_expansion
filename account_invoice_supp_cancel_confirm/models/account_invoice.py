# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


    
class AccountInvoiceCancelConfirmed(models.TransientModel):
    _name = "account.invoice.cancel.wizard.confirmed"
    _description = "Wizard para cancelar la Factura de Proveedor"

    notes_cancel = fields.Text('Motivo de Cancelacion', required=True)


    @api.multi
    def action_cancel(self):
        self.ensure_one()
        active_ids = self._context.get('active_ids', []) or []

        invoice_br = self.env['account.invoice'].browse(active_ids)
        mensaje_notas_cancelacion = "La Factura <strong> %s </strong>fue cancelada por el Usuario <strong> %s </strong>.<br/>Motivo de la Cancelacion: <strong> %s </strong>" % (invoice_br.number, self.env.user.name, self.notes_cancel)
        invoice_br.message_post(body=mensaje_notas_cancelacion)
        invoice_br.action_cancel()
        return {'type': 'ir.actions.act_window_close'}
    