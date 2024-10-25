# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, RedirectWarning, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
#from pytz import timezone
#import pytz
import time
import logging
_logger = logging.getLogger(__name__)


class PurchaseRequisition(models.Model):
    _inherit ='purchase.requisition'

    def _get_current_date_fp(self):
        return fields.Date.context_today(self)

    ordering_date = fields.Date('Fecha Pedido', default=_get_current_date_fp)

    # state_authorized = fields.Selection([('pendiente','Pendiente'),('autorizado','Autorizado')], 
    #             'Autorizacion', compute='_metodo_authorized', store=True, default='pendiente')

    # def _metodo_authorized(self):
    #     for rec in self:
    #         all_ok = False
    #         all_authorized_list = []
    #         for line in rec.line_ids:
    #             if line.x_authorized_by:
    #                 all_authorized_list.append(True)
    #             else:
    #                 all_authorized_list.append(False)
    #         if False in all_authorized_list:
    #             return 'pendiente'
    #         else:
    #             return 'autorizado'



    # @api.multi
    # def action_in_progress(self):
    #     res = super(PurchaseRequisition, self).action_in_progress()
    #     for rec in self:
    #         all_ok = False
    #         all_authorized_list = []
    #         for line in rec.line_ids:
    #             if not line.x_authorized_by:
    #                 raise UserError("Error!\nEl Producto %s aún no se encuentra Autorizado." % line.product_id.name)
    #             if line.x_authorized_by:
    #                 all_authorized_list.append(True)
    #             else:
    #                 all_authorized_list.append(False)
    #         if False in all_authorized_list:
    #             rec.state_authorized = 'pendiente'
    #         else:
    #             rec.state_authorized =  'autorizado'

    #     return res



    # @api.multi
    # def action_open(self):
    #     res = super(PurchaseRequisition, self).action_open()
    #     for rec in self:
    #         all_ok = False
    #         all_authorized_list = []
    #         for line in rec.line_ids:
    #             if not line.x_authorized_by:
    #                 raise UserError("Error!\nEl Producto %s aún no se encuentra Autorizado." % line.product_id.name)
    #             if line.x_authorized_by:
    #                 all_authorized_list.append(True)
    #             else:
    #                 all_authorized_list.append(False)
    #         if False in all_authorized_list:
    #             rec.state_authorized = 'pendiente'
    #         else:
    #             rec.state_authorized =  'autorizado'

    #     return res

class PurchaseRequisitionLine(models.Model):
    _inherit = "purchase.requisition.line"

    @api.multi
    def _prepare_purchase_order_line(self, name, product_qty=0.0, price_unit=0.0, taxes_ids=False):
        purchase_order_line = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name=name,
                                                                                product_qty=product_qty,
                                                                                price_unit=price_unit,
                                                                                taxes_ids=taxes_ids)
        if self.x_store_id:
            purchase_order_line['store_id'] = self.x_store_id.id
        return purchase_order_line


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def _prepare_invoice_line(self):
        invoice_line = super(AccountInvoiceLine, self)._prepare_purchase_order_line()
        if self.purchase_line_id:
            if self.purchase_line_id.store_id:
                invoice_line['x_store_id'] = self.purchase_line_id.store_id.id
        return invoice_line

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def _prepare_invoice_line_from_po_line(self, line):
        # Preparar los valores de la línea de factura desde la línea de compra
        res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
        # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
        if line.store_id:
            res['x_store_id'] = line.store_id.id
        return res

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        for invoice in self:
            if invoice.type == 'in_invoice':
                for invoice_line in invoice.invoice_line_ids:
                    # Filtrar la línea de apunte correspondiente al producto de la línea de factura
                    move_line = invoice.move_id.line_ids.filtered(lambda l: l.product_id == invoice_line.product_id)
                    # Asignar el valor de x_store_id a store_id en la línea de apunte
                    if move_line and invoice_line.x_store_id:
                        move_line.write({'store_id': invoice_line.x_store_id.id})
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        # Crear la factura de proveedor
        invoice = super(AccountInvoice, self).create(vals)
        for line in invoice.invoice_line_ids:
            if line.purchase_line_id and line.purchase_line_id.store_id:
                # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
                line.x_store_id = line.purchase_line_id.store_id.id
        return invoice

class StockPicking(models.Model):
    _inherit = 'stock.picking'

class StockMove(models.Model):
    _inherit = 'stock.move'


    # def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id):
    #     print ("########### _generate_valuation_lines_data >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    #     # Llama al método original para obtener los datos básicos
    #     rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id)
        
    #     # Agregar el store_id en los valores de `credit_line_vals` y `debit_line_vals`
    #     store_id = self.picking_id.store_id.id if self.picking_id.store_id else False   # Obtiene el ID de `store_id` del movimiento de inventario
    #     print ("################## store_id: ", store_id)
    #     if store_id:
    #         if 'debit_line_vals' in rslt:
    #             rslt['debit_line_vals'].update({
    #                 'store_id': store_id,
    #             })
            
    #         if 'credit_line_vals' in rslt:
    #             rslt['credit_line_vals'].update({
    #                 'store_id': store_id,
    #             })
            
    #         if 'price_diff_line_vals' in rslt:
    #             rslt['price_diff_line_vals'].update({
    #                 'store_id': store_id,
    #             })
            
    #     return rslt

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        if self.picking_id and self.picking_id.store_id:
            res[0][2].update({'store_id': self.picking_id.store_id.id if self.picking_id.store_id else False })
            res[1][2].update({'store_id': self.picking_id.store_id.id if self.picking_id.store_id else False })
        return res        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
