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
        print ("######## _prepare_purchase_order_line >>>>>>>>>>>> ")
        purchase_order_line = super(PurchaseRequisitionLine, self)._prepare_purchase_order_line(name=name,
                                                                                product_qty=product_qty,
                                                                                price_unit=price_unit,
                                                                                taxes_ids=taxes_ids)
        if self.x_store_id:
            purchase_order_line['store_id'] = self.x_store_id.id
        print ("#################### self.x_store_id: ", self.x_store_id)
        print ("#################### purchase_order_line: ", purchase_order_line)
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

    # @api.multi
    # def _prepare_invoice_line_from_po_line(self, line):
    #     # Preparar los valores de la línea de factura desde la línea de compra
    #     res = super(AccountInvoice, self)._prepare_invoice_line_from_po_line(line)
    #     print ("########## RES: ", res)
    #     # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
    #     if line.store_id:
    #         res['x_store_id'] = line.store_id.id
    #     return res

    # Load all unsold PO lines
    @api.onchange('purchase_id')
    def purchase_order_change(self):
        print ("######### purchase_order_change>>>>>>>>>>>>>>>>>>>>> ")
        print ("######### purchase_order_change>>>>>>>>>>>>>>>>>>>>> ")
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        vendor_ref = self.purchase_id.partner_ref
        if vendor_ref and (not self.reference or (
                vendor_ref + ", " not in self.reference and not self.reference.endswith(vendor_ref))):
            self.reference = ", ".join([self.reference, vendor_ref]) if self.reference else vendor_ref

        if not self.invoice_line_ids:
            #as there's no invoice line yet, we keep the currency of the PO
            self.currency_id = self.purchase_id.currency_id

        new_lines = self.env['account.invoice.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            data = self._prepare_invoice_line_from_po_line(line)
            print ("######### line.store_id: ", line.store_id)
            if line.store_id:
                # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
                data['x_store_id'] = line.store_id.id
            new_line = new_lines.new(data)
            new_line._set_additional_fields(self)
            new_lines += new_line

        self.invoice_line_ids += new_lines
        self.payment_term_id = self.purchase_id.payment_term_id
        self.env.context = dict(self.env.context, from_purchase_order_change=True)
        self.purchase_id = False
        return {}

    @api.model
    def invoice_line_move_line_get(self):
        # Llama al método original
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        # Agrega `x_sucursal_id` a cada línea en `res` si está presente en la línea de factura
        for line in res:
            # Busca la línea de factura original con el `invl_id`
            invoice_line = self.env['account.invoice.line'].browse(line['invl_id'])
            
            # Verifica si `x_sucursal_id` existe y lo agrega al diccionario `line`
            if hasattr(invoice_line, 'x_store_id') and invoice_line.x_store_id:
                line['store_id'] = invoice_line.x_store_id.id

        return res
        
class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def create(self, vals):
        print  ("############ create >>>>>>>>>>> ")
        # Crear la factura de proveedor
        invoice = super(AccountInvoice, self).create(vals)
        for line in invoice.invoice_line_ids:
            print  ("############ line.purchase_line_id: ",line.purchase_line_id)
            print  ("############ line.purchase_line_id.store_id: ",line.purchase_line_id.store_id)
            if line.purchase_line_id and line.purchase_line_id.store_id:
                # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
                line.x_store_id = line.purchase_line_id.store_id.id
        return invoice

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        result['context'] = {
            'type': 'in_invoice',
            'default_purchase_id': self.id,
            'default_currency_id': self.currency_id.id,
            'default_company_id': self.company_id.id,
            'company_id': self.company_id.id
        }
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.invoice_supplier_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        res_id = result.get('res_id', False)
        print  ("############ res_id: ",res_id)
        if res_id:
            invoice_br = self.env['account.invoice'].browse(res_id)
            for line in invoice_br.invoice_line_ids:
                print  ("############ line.purchase_line_id: ",line.purchase_line_id)
                print  ("############ line.purchase_line_id.store_id: ",line.purchase_line_id.store_id)
                if line.purchase_line_id and line.purchase_line_id.store_id:
                    # Pasar el valor de store_id de la línea de compra a x_store_id en la línea de factura
                    line.x_store_id = line.purchase_line_id.store_id.id
        result['context']['default_origin'] = self.name
        result['context']['default_reference'] = self.partner_ref
        return result

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    store_id = fields.Many2one('res.store', string="Sucursal", readonly=False)

class StockPicking(models.Model):
    _inherit = 'stock.picking'

################# Sucursal en las Polizas #########################
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
        if self.picking_id and self.picking_id.quotation_store_id:
            res[0][2].update({'store_id': self.picking_id.quotation_store_id.id if self.picking_id.quotation_store_id else False })
            res[1][2].update({'store_id': self.picking_id.quotation_store_id.id if self.picking_id.quotation_store_id else False })
        return res

    def _account_entry_move(self):
        res = super(StockMove, self)._account_entry_move()
        picking_store_id = self.picking_id.quotation_store_id
        if picking_store_id:
            moves_res = self.env['account.move']
            for move in self.picking_id.move_lines:
                moves_res |= move.account_move_ids
            for poliza_prev in moves_res:
                poliza_prev.store_id = picking_store_id.id
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
