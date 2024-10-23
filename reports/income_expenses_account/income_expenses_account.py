# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
 
from datetime import datetime, timedelta, date #Libreria para obtener la fecha actual
import base64
import csv
import time
import dateutil
import dateutil.parser
from dateutil.relativedelta import relativedelta

import time
import sys

from odoo import api, fields, models, _, tools, release
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from odoo.tools import float_compare, float_round



# class account_move_line(osv.osv):
#     _name = "account.move.line"
#     _inherit = 'account.move.line'
#     _columns = {
#         'invoice_voucher_id = fields.many2one('account.invoice', 'Invoice Reference', ondelete='cascade', select=True),
#     }

# account_move_line()

class wizard_income_expenses(models.TransientModel):
    _name = 'wizard.income.expenses'
    _description = 'Generacion de Reporte Ingresos y Egresos'


    partner_id = fields.Many2one('res.partner', 'Cliente', change_default=True, select=True)
    date =  fields.Date('Fecha Inicial', required=True, default=fields.Date.today())
    date_end =  fields.Date('Fecha Final', required=True, default=fields.Date.today())
    report_type =  fields.Selection([('ingresos','Ingresos'),('egresos','Egresos')], 'Tipo', required=True)


    def generate_report_income_expenses(self):
        cr  = self.env.cr
        context = self._context
        #print '########################----->que ondaaaa'
        mybr = self
        partner_id= mybr.partner_id
        date_in= mybr.date
        date_end= mybr.date_end
        report_type= mybr.report_type
        cr.execute('delete from account_inc_exp', ())

        account_obj = self.env['account.payment'].sudo()
        account_move_obj = self.env['account.move.line'].sudo()
        account_invoice_obj=self.env['account.invoice'].sudo()

        account_inc_exp_obj=self.env['account.inc.exp'].sudo()
        partner_obj=self.env['res.partner'].sudo()
        accountmove_obj = self.env['account.move'].sudo()
        account_journal_obj = self.env['account.journal'].sudo()
        account_account_obj = self.env['account.account'].sudo()
        account_tax_obj = self.env['account.invoice.tax'].sudo()
        tax_cat_obj = self.env['account.tax'].sudo()
        account_invoice_line_obj = self.env['account.invoice.line'].sudo()
        product_obj = self.env['product.product'].sudo()
        parter_obj = self.env['res.partner'].sudo()
        parter_obj = self.env['res.partner'].sudo()
        res_currency_rate_obj = self.env['res.currency.rate'].sudo()
        invoice_linetax = self.env['account.invoice.line.tax'].sudo()
        generate_ids = []
        ban_pas=False

        


        if report_type == 'egresos':
            report_type = 'payment'
            #print report_type
        else:
            report_type = 'receipt'
            #print report_type
        
        #print date_in
        #print date_end
        if partner_id:
            #print partner_id
            partner_browse = partner_obj.browse(partner_id.id)
            #print partner_browse
            if partner_browse.customer == False and report_type == 'receipt':
                raise osv.except_osv(_('Processing Error!'), _('El Partner Seleccionado corresponde a un Proveedor y esta intentando generar Ingresos. Seleccione un Cliente.') \
                                % ())
            elif partner_browse.customer == True and report_type == 'payment':
                raise osv.except_osv(_('Processing Error!'), _('El Partner Seleccionado corresponde a un Cliente y esta intentando generar Egresos. Seleccione un Proveedor.') \
                                % ())

                                

        if partner_id and date_in and date_end and report_type:
        #     print 'partner_id',partner_id
        #     print 'date_end',date_end
        #     print 'date_in',date_in
        #     print 'report_type',report_type
            account_search = account_obj.search(['&',('partner_id','=',partner_id.id),('date','>=',date_in),('date','<=',date_end),('type','=',report_type),('state','=','posted')])
            #print account_search
            if account_search:
                account_browse = account_search
                for account in account_browse:
                    #print '1.- id account voucher',account.id
                    account_line_search = account_line_obj.search(['&',('voucher_id','=',account.id),('amount','!=',0)])
                    if account_line_search:
                        account_line_browse = account_line_search
                        for line in account_line_browse:
                            #print 'account voucher line',line.id
                            id_move=line.move_line_id.id
                            if id_move:
                                account_move_search = account_move_obj.search([('id','=',id_move)])
                            if account_move_search:
                                account_move_browse = account_move_search
                                for move in account_move_browse:
                                    #print 'account move line',move.id
                                    #print 'account move',move.move_id.id
                                    account_invoice_search = account_invoice_obj.search([('move_id','=',move.move_id.id)])
                                    if account_invoice_search:
                                        gravado=0.0
                                        iva=0.0
                                        iva_ret=0.0
                                        iva_hon=0.0
                                        ieps=0.0
                                        isr_ret=0.0
                                        excento = 0.0
                                        fletes=0.0
                                        fleteret=0.0
                                        otros = 0.0
                                        monto_iva = 0.0
                                        iva_excento=0.0
                                        iva_cero=0.0
                                        bantax= False
                                        iva_name=False

                                        account_invoice_browse = account_invoice_search[0]

                                        #print 'account invoice',account_invoice_browse.id

                                        #print "################################################################"
                                        #print "id de la factura",account_invoice_browse.id
                                        #print "supplier_invoice_number factura",account_invoice_browse.supplier_invoice_number
                                        #print "internal_number factura",account_invoice_browse.internal_number


                                        partner_browse = account_invoice_browse.partner_id
                                        if account.move_id.id:
                                            amove_browse = account.move_id
                                            account_mov = account_move_obj.search([('move_id','=',account.move_id.id)])
                                            #print account.move_id.id

                                        journal_browse = account.journal_id
                                        accounta_browse = account.account_id

                                        if report_type == 'payment':
                                            #-------------------------
                                            account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','!=',False),('debit','!=','0.0')])
                                            #print "-->",account_movss
                                            if not account_movss:
                                                    account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','=',28)])
                    
                                            if account_movss:
                                                account_mov_browse = account_movss
                                                for move_ac in account_mov_browse:

                                                    iva_name=False
                                                   
                                                    if account_invoice_browse.supplier_invoice_number:
                                                        inv_num=account_invoice_browse.supplier_invoice_number[0:14]
                                                        #print 'if uno'
                                                        if inv_num in move_ac.name:
                                                            #print 'supplier_invoice',account_invoice_browse.supplier_invoice_number,'en',move_ac.name
                                                            iva_name=True
                                                    if account_invoice_browse.internal_number:
                                                        if account_invoice_browse.internal_number in move_ac.name:
                                                            #print 'account_invoice_browse',account_invoice_browse.internal_number,'en',move_ac.name
                                                            iva_name=True



                                                    if iva_name:#account_invoice_browse.supplier_invoice_number or account_invoice_browse.internal_number in move_ac.name: #or move_ac.invoice_voucher_id.id:
                                                        #print 'si paso'

                            
                                                        if move_ac.tax_id_secondary:

                                                            tax_mov = tax_cat_obj.search([('id','=',move_ac.tax_id_secondary.id),('tax_voucher_ok','=',True),('account_paid_voucher_id','=',move_ac.account_id.id)])
                                                            if tax_mov:
                                                                ban_pas=True
                                                                tax_mov_browse = tax_mov
                                                                for taxm in tax_mov_browse:
                                                                    if move_ac.credit:
                                                                        monto_total=move_ac.credit
                                                                        #print 'credit',monto_total
                                                                    else:
                                                                        monto_total=move_ac.debit
                                                                        #print 'debit',monto_total
                                                                    if taxm.tax_diot == 'tax_16':
                                                                        bantax=True
                                                                        iva = monto_total
                                                                        #print 'ivaaaa',iva
                                                                        gravado=iva/.16
                                                                        #print iva
                                                                    elif taxm.tax_category_id.id == 1:
                                                                        if 'HON' in taxm.name or 'hon' in taxm.name:
                                                                            #print "HON##########2",monto_total
                                                                            iva_hon = monto_total
                                                                        else:
                                                                            iva_ret = monto_total
                                                                        #print "---->",iva_ret
                                                                    elif taxm.tax_category_id.id == 5:
                                                                        isr_ret = monto_total
                                                                        #print isr_ret
                                                                        #print iva_hon
                                                                    elif taxm.tax_category_id.id == 6:
                                                                        ieps = monto_total
                                                                        #print ieps
                                                                    elif taxm.tax_category_id.id == 3:
                                                                        iva_excento=monto_total
                                                                        excento=line.amount
                                                                        #print '------->>>>>>',iva_excento
                                                                    elif taxm.tax_category_id.id == 9:
                                                                        iva_cero=monto_total
                                                                        #print iva_cero
                                                        #print '#####',bantax
                                                        #print 'ivaaaaint',iva
                                                        if not bantax == True:
                                                            excento=line.amount
                                                        else:
                                                            subtotal_grav = iva+gravado
                                                            subtotal_final = line.amount-subtotal_grav
                                                            if not subtotal_final < 1:
                                                                excento = subtotal_final
                                                            else:
                                                                excento = 0.0
                                                        #print 'ivaaaait2',iva
                                        else:
                                            account_movss = account_move_obj.search( [('move_id','=',account.move_id.id),('tax_id_secondary','!=',False)])
                                            if not account_movss:
                                                account_movss = account_move_obj.search( [('move_id','=',account.move_id.id),('tax_id_secondary','=',28)])
                                                #print "-->",account_movss
                                                #print account.move_id.id
                                            if account_movss:
                                                account_mov_browse = account_movss
                                                # if account_mov:
                                                #     #inv_num=""
                                                #     account_mov_browse = account_move_obj.browse(cr, uid,account_mov, context=None)
                                                for move_ac in account_mov_browse:
                                                    if account_invoice_browse.internal_number in move_ac.name:

                                                        if move_ac.tax_id_secondary:

                                                            tax_mov = tax_cat_obj.search([('id','=',move_ac.tax_id_secondary.id),('tax_voucher_ok','=',True),('account_paid_voucher_id','=',move_ac.account_id.id)])
                                                            if tax_mov:
                                                                ban_pas=True
                                                                tax_mov_browse = tax_mov
                                                                for taxm in tax_mov_browse:
                                                                    if move_ac.credit:
                                                                        monto_total=move_ac.credit
                                                                    else:
                                                                        monto_total=move_ac.debit
                                                                    if taxm.tax_diot == 'tax_16':
                                                                        bantax=True
                                                                        iva = monto_total
                                                                        #print 'ivvvvvvvvvvvvv------------>>>>>',iva
                                                                        gravado=iva/.16
                                                                        #print iva
                                                                    elif taxm.tax_category_id.id == 1:
                                                                        if 'HON' in taxm.name or 'hon' in taxm.name:
                                                                            iva_hon = monto_total
                                                                        else:
                                                                            iva_ret = monto_total
                                                                        #print "---->",iva_ret
                                                                    elif taxm.tax_category_id.id == 5:
                                                                        isr_ret = monto_total
                                                                        #print isr_ret
                                                                        #print iva_hon
                                                                    elif taxm.tax_category_id.id == 6:
                                                                        ieps = monto_total
                                                                        #print ieps
                                                                    elif taxm.tax_category_id.id == 3:
                                                                        iva_excento=monto_total
                                                                        excento=line.amount
                                                                        #print '22222222',iva_excento
                                                                    elif taxm.tax_category_id.id == 9:
                                                                        iva_cero=monto_total
                                                                        #print iva_cero
                                                        #print '#####',bantax
                                                        if not bantax == True:
                                                            excento=line.amount
                                                        else:
                                                            subtotal_grav = iva+gravado
                                                            subtotal_final = line.amount-subtotal_grav
                                                            if not subtotal_final < 1:
                                                                excento = subtotal_final
                                                            else:
                                                                excento = 0.0

                                       #impuestos
                                        if not ban_pas:
                                                #print 'linea guia',line.id
                                            cr.execute("""
                                            select id,tax_id from account_voucher_line_tax
                                            where voucher_line_id='%s' ;
                                                """ % line.id)
                                            cr_res = cr.fetchall()

                                            if cr_res:
                                                for cr_ in cr_res:
                                                        #id_imp.append(cr_[0])
                                                        #print '=====>>>',cr_[0]

                                                        #----------------------------------
                                                    cr.execute("""
                                                    select credit,name from account_move_line
                                                    where tax_id='%s' and credit!=0 ;
                                                        """ % cr_[0])
                                                    cr_prub = cr.fetchall()
                                                        #print '--->',cr_prub
                                                        #time.sleep(4)
                                                        #-----------------------------------

                                                    if cr_prub:
                                                        for prub_cr in cr_prub:

                                                            account_cat_browse = tax_cat_obj.browse([cr_[1]])[0]
                                                               
                                                            if account_cat_browse.tax_diot == 'tax_16':
                                                                if not bantax:
                                                                    iva = prub_cr[0]
                                                                    bantax=True
                                                                    gravado=iva/.16
                                                               
                                                            if account_cat_browse.tax_category_id.id == 1 and not 'HON' in prub_cr[1] and iva_ret==0:
                                                                iva_ret = prub_cr[0]
                                                                #print "-->>>",iva_ret
                                                            elif account_cat_browse.tax_category_id.id == 5 and isr_ret ==0:
                                                                isr_ret = prub_cr[0]
                                                            elif 'HON' in prub_cr[1] or 'hon' in prub_cr[1] and iva_hon==0:
                                                                iva_hon = prub_cr[0]
                                                            elif account_cat_browse.tax_category_id.id == 6 and ieps==0:
                                                                ieps = prub_cr[0]
                                            if not bantax == True:
                                                excento=line.amount
                                            else:
                                                subtotal_grav = iva+gravado
                                                subtotal_final = line.amount-subtotal_grav
                                                if not subtotal_final < 1:
                                                    excento = subtotal_final
                                                else:
                                                    excento = 0.0
                                        fecha_rep=account.date[6:7]
                                        if str(fecha_rep) == '9':
                                                #print 'entreeeee'
                                            account_tax_search = account_tax_obj.search([('invoice_id','=',account_invoice_browse.id)])
                                                    #print 'ivaa2',iva
                                            if account_tax_search:
                                                account_tax_browse = account_tax_search
                                                if not account.amount == 0.0:
                                                    for tax in account_tax_browse:
                                                        if tax.tax_id.id:
                                                            account_cat_browse = tax.tax_id
                                                    
                                                            if account_cat_browse.tax_diot == 'tax_16':
                                                                iva = tax.amount
                                                            elif account_cat_browse.tax_category_id.id == 1 and not 'HON' in tax.name and iva_ret==0:
                                                                iva_ret = tax.amount*-1
                                                                        #print "-->>>",iva_ret
                                                            elif account_cat_browse.tax_category_id.id == 5 and isr_ret ==0:
                                                                isr_ret = tax.amount
                                                            elif 'HON' in tax.name or 'hon' in tax.name and iva_hon==0:
                                                                iva_hon = tax.amount
                                                            elif account_cat_browse.tax_category_id.id == 6 and ieps==0:
                                                                ieps = tax.amount
                                            if not bantax == True:
                                                excento=line.amount
                                            else:
                                                subtotal_grav = iva+gravado
                                                subtotal_final = line.amount-subtotal_grav
                                                if not subtotal_final < 1:
                                                    excento = subtotal_final
                                                else:
                                                    excento = 0.0
                                            #--------------------------------------------        
                                        
                                        account_inline_search = account_invoice_line_obj.search([('invoice_id','=',account_invoice_browse.id)])
                                        if account_inline_search:
                                            account_inline_browse = account_inline_search
                                            for inline in account_inline_browse:

                                                
                                                #print 'product_id',inline.product_id
                                                product_search = product_obj.search([('id','=',inline.product_id.id)])
                                                if product_search:
                                                    product_browse = product_search[0]
                                                    if not account.amount == 0.0:
                                                        if product_browse.tms_category == 'freight':
                                                            fletes=fletes+inline.price_subtotal
                                                        else:
                                                            otros=otros+inline.price_subtotal
                                            # MODIFICACION FLETES------------>>>

                                            if not fletes == 0:
                                                if not otros == 0:
                                                    if not iva == 0.0:
                                                        if not iva_ret == 0.0:
                                                            fletes = (iva_ret*-1)/.04
                                                            otros = (iva/.16)-fletes
                                                            #fletes = (line.amount-(iva-(iva_ret*-1)))/2
                                                            #otros = (line.amount-(iva-(iva_ret*-1)))/2
                                                        #else:
                                                        #    fletes = (line.amount-iva)/2
                                                        #    otros = (line.amount-iva)/2
                                                        else:
                                                            fletes = 0.0
                                                            fleteret=iva/.16
                                                            otros= 0.0
                                                    #else:
                                                    #    if not iva_ret == 0.0:
                                                    #        fletes = (line.amount-(iva_ret)*-1)/2
                                                    #        otros = (line.amount-(iva_ret)*-1)/2
                                                    #    else:
                                                    #        fletes = line.amount/2
                                                    #        otros = line.amount/2
                                                else:
                                                    if not iva==0.0:
                                                        if not iva_ret == 0.0:
                                                            fletes=(iva_ret*-1)/.04
                                                        else:
                                                            fletes = iva/.16
                                                    #else:
                                                    #    if not iva_ret == 0.0:
                                                    #        fletes = (line.amount-(iva_ret*-1))
                                                    #    else:
                                                    #        fletes = line.amount
                                            else:
                                                if not otros == 0:
                                                    if not iva == 0.0:
                                                        #if not iva_ret == 0.0:
                                                        #    otros = (line.amount-(iva-(iva_ret*-1)))
                                                        #else:
                                                        otros = iva/.16

                                        #print 'ivaa3',iva
                                        ajournal_search= account_journal_obj.search([('id','=',account.journal_id.id)])
                                        if ajournal_search:
                                            #print 'etreeee'
                                            ajournal_browse= ajournal_search[0]

                                        if ajournal_browse.currency.id == 3:

                                            currency_rate_search=res_currency_rate_obj.search([('currency_id','=',account_invoice_browse.currency_id.id),('name','=',account.date)])
                                            if currency_rate_search:
                                                #print 'entreeeee'
                                                currency_rate_browse = currency_rate_search[0]
                                                ratem = currency_rate_browse.rate
                                            else:
                                                #print 'aquiii'
                                                ratem = account_invoice_browse.currency_id.rate

                                            #print 'ratemmmmmm',ratem
                                            rate=1/ratem

                                            total = round(rate*line.amount,2)
                                            monto_iva=round(rate*account.amount,2)#round(rate*monto_iva,2)

                                        else:
                                            total=round(line.amount,2)
                                            monto_iva=round(account.amount,2)
                                        
                                        if account_invoice_browse.type == 'out_refund' or account_invoice_browse.type == 'in_refund':
                                            iva=iva*-1
                                            iva_ret=iva_ret*-1
                                            total=total*-1
                                            gravado=gravado*-1
                                            excento=excento*-1
                                            isr_ret=isr_ret*-1
                                            iva_hon=iva_hon*-1
                                            ieps=ieps*-1
                                            monto_iva=monto_iva*-1
                                            iva_excento=iva_excento*-1
                                            iva_cero=iva_cero*-1
                                            fletes=fletes*-1
                                            fleteret=fleteret*-1
                                            otros=otros*-1
                                        #print "-------------", account_invoice_browse.number
                                        #print "iva final",iva


                                        #--------------EGRESOS-------------
                                        if report_type == 'payment':
                                            income_expenses_line = {
                                                'tipo': report_type,
                                                'rfc': partner_browse.vat,
                                                'name': partner_browse.name,
                                                'type_journal': journal_browse.name,
                                                'name_journal': amove_browse.name,
                                                'date_journal': amove_browse.date,
                                                'date_voucher': account.date,
                                                'bank': journal_browse.name,
                                                'number_account': account_invoice_browse.number,
                                                'folio_account': account_invoice_browse.supplier_invoice_number,
                                                'iva': iva,
                                                'iva_ret': iva_ret,
                                                'total': total,
                                                'count': accounta_browse.name,
                                                'date_invoice': account_invoice_browse.date_invoice,
                                                'gravado': gravado,
                                                'exento': excento,
                                                'isr_ret': isr_ret,
                                                'iva_hon': iva_hon,
                                                'ieps': ieps,
                                                'monto_iva': monto_iva,
                                                'iva_excento': iva_excento,
                                                'iva_cero': iva_cero,
            
                                            }
                                            generate_ids.append(account_inc_exp_obj.create(income_expenses_line).id)
                                        else:
                                            income_expenses_line = {
                                                'tipo': report_type,
                                                'rfc': partner_browse.vat,
                                                'name': partner_browse.name,
                                                'type_journal': journal_browse.name,
                                                'name_journal': amove_browse.name,
                                                'date_journal': amove_browse.date,
                                                'date_voucher': account.date,
                                                'bank': journal_browse.name,
                                                'number_account': account_invoice_browse.number,
                                                'folio_account': account_invoice_browse.supplier_invoice_number,
                                                'date_invoice': account_invoice_browse.date_invoice,
                                                'flete': fletes,
                                                'fleteret':fleteret,
                                                'other': otros,
                                                'iva': iva,
                                                'iva_ret': iva_ret,
                                                'total': total,
                                                'monto_iva': monto_iva,
                                                'iva_excento': iva_excento,
                                                'iva_cero': iva_cero,
                                            }
                                            generate_ids.append(account_inc_exp_obj.create(income_expenses_line).id)



        else:
            if date_in and date_end and report_type:

                account_search = account_obj.search(['&',('date','>=',date_in),('date','<=',date_end),('type','=',report_type),('state','=','posted')])
                #print account_search
                if account_search:
                    account_browse = account_search
                    for account in account_browse:
                        #print '1.-id account voucher',account.id
                        #print account.name
                        account_line_search = account_line_obj.search(['&',('voucher_id','=',account.id),('amount','!=',0)])
                        if account_line_search:
                            account_line_browse = account_line_search
                            for line in account_line_browse:
                                #print 'account voucher line',line.id
                                id_move=line.move_line_id.id
                                if id_move:
                                    account_move_search = account_move_obj.search([('id','=',id_move)])
                                if account_move_search:
                                    account_move_browse = account_move_search
                                    for move in account_move_browse:
                                        #print 'account move line',move.id
                                        #print 'account move',move.move_id.id
                                        account_invoice_search = account_invoice_obj.search([('move_id','=',move.move_id.id)])
                                        if account_invoice_search:
                                            gravado=0.0
                                            iva=0.0
                                            iva_ret=0.0
                                            iva_hon=0.0
                                            ieps=0.0
                                            isr_ret=0.0
                                            excento = 0.0
                                            fletes=0.0
                                            fleteret=0.0
                                            otros=0.0
                                            monto_iva = 0.0
                                            iva_excento=0.0
                                            iva_cero=0.0
                                            bantax= False
                                            ban_pas=False
                                            #print "ban_passs",ban_pas

                                            account_invoice_browse = account_invoice_search[0]
                                            #print 'account invoice',account_invoice_browse.id



                                            partner_browse = account_invoice_browse.partner_id
                                            if account.move_id.id:
                                                amove_browse = account.move_id
                                                account_mov = account_move_obj.search([('move_id','=',account.move_id.id)])
                                            journal_browse = account.journal_id
                                            accounta_browse = account.account_id

                                            if report_type == 'payment':
                                                #print 'pyyyymentttt'
                                                #-------------------------
                                                #print "account_voucher",account.id
                                                account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','!=',False),('debit','!=','0.0')])
                                                if not account_movss:
                                                    account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','=',28)])
                                                
                                                
                                                #print account.move_id.id
                                                if account_movss:
                                                    account_mov_browse = account_movss
                                                    for move_ac in account_mov_browse:

                                                        iva_name=False

                                                        if account_invoice_browse.supplier_invoice_number:
                                                            inv_num=account_invoice_browse.supplier_invoice_number[0:14]
                                                            if inv_num in move_ac.name:
                                                                #print 'supplier_invoice',account_invoice_browse.supplier_invoice_number,'en',move_ac.name
                                                                iva_name=True
                                                        if account_invoice_browse.internal_number:
                                                            if account_invoice_browse.internal_number in move_ac.name:
                                                                #print 'account_invoice_browse',account_invoice_browse.internal_number,'en',move_ac.name
                                                                iva_name=True



                                                        if iva_name:#account_invoice_browse.supplier_invoice_number or account_invoice_browse.internal_number in move_ac.name: #or move_ac.invoice_voucher_id.id:

                                                            if move_ac.tax_id_secondary:

                                                                tax_mov = tax_cat_obj.search([('id','=',move_ac.tax_id_secondary.id),('tax_voucher_ok','=',True),('account_paid_voucher_id','=',move_ac.account_id.id)])
                                                                if tax_mov:
                                                                    ban_pas=True
                                                                    tax_mov_browse = tax_mov
                                                                    for taxm in tax_mov_browse:
                                                                        if move_ac.credit:
                                                                            monto_total=move_ac.credit
                                                                            #print 'credit',monto_total
                                                                        else:
                                                                            monto_total=move_ac.debit
                                                                            #print 'debit',monto_total
                                                                        if taxm.tax_diot == 'tax_16':
                                                                            bantax=True
                                                                            iva = monto_total
                                                                            #print 'ivaaaaaaaaaaaaaaaaaaa--->',iva
                                                                            gravado=iva/.16
                                                                            #print iva
                                                                        elif taxm.tax_category_id.id == 1:
                                                                            if 'HON' in taxm.name or 'hon' in taxm.name:
                                                                                #print "HON##########2",monto_total
                                                                                iva_hon = monto_total
                                                                            else:
                                                                                iva_ret = monto_total
                                                                            #print "---->",iva_ret
                                                                        elif taxm.tax_category_id.id == 5:
                                                                            isr_ret = monto_total
                                                                            #print isr_ret
                                                                            #print iva_hon
                                                                        elif taxm.tax_category_id.id == 6:
                                                                            ieps = monto_total
                                                                            #print ieps
                                                                        elif taxm.tax_category_id.id == 3:
                                                                            iva_excento=monto_total
                                                                            excento=line.amount
                                                                            #print '33333',iva_excento
                                                                        elif taxm.tax_category_id.id == 9:
                                                                            iva_cero=monto_total
                                                                            #print iva_cero
                                                            #print '#####',bantax
                                                            #print 'ivaaaaint',iva
                                                            if not bantax == True:
                                                                excento=line.amount
                                                            else:
                                                                subtotal_grav = iva+gravado
                                                                subtotal_final = line.amount-subtotal_grav
                                                                if not subtotal_final < 1:
                                                                    excento = subtotal_final
                                                                else:
                                                                    excento = 0.0
                                                            #print 'ivaaaait2',iva
                                                #print "impuestos",iva,"--",iva_ret,"--",ieps,"---",isr_ret
                                            else:
                                                account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','!=',False)])
                                                if not account_movss:
                                                    account_movss = account_move_obj.search([('move_id','=',account.move_id.id),('tax_id_secondary','=',28)])
                                                #print "-->",account_movss
                                                #print account.move_id.id
                                                if account_movss:
                                                    account_mov_browse = account_movss
                                                # if account_mov:
                                                #     #inv_num=""
                                                #     account_mov_browse = account_move_obj.browse(cr, uid,account_mov, context=None)
                                                    for move_ac in account_mov_browse:

                                                        if account_invoice_browse.internal_number in move_ac.name:

                                                            if move_ac.tax_id_secondary:
                                                                ban_pas=True
                                                                #print 'if1'
                                                                #print move_ac.account_id.id
                                                                #print move_ac.tax_id_secondary.id
                                                                tax_mov = tax_cat_obj.search([('id','=',move_ac.tax_id_secondary.id),('tax_voucher_ok','=',True),('account_paid_voucher_id','=',move_ac.account_id.id)])
                                                                if tax_mov:
                                                                    #print 'if2'
                                                                    tax_mov_browse = tax_mov
                                                                    for taxm in tax_mov_browse:
                                                                        #print 'cat',taxm.tax_category_id.id
                                                                        if move_ac.credit:
                                                                            monto_total=move_ac.credit
                                                                        else:
                                                                            monto_total=move_ac.debit
                                                                        if taxm.tax_diot == 'tax_16':
                                                                            bantax=True
                                                                            iva = monto_total
                                                                            gravado=iva/.16
                                                                            #print 'ivaaaaaaaaa---->>>>>>><<2',iva
                                                                        elif taxm.tax_category_id.id == 1:
                                                                            #print 'ivaaa_ret'
                                                                            if 'HON' in taxm.name or 'hon' in taxm.name:
                                                                                iva_hon = monto_total
                                                                            else:
                                                                                iva_ret = monto_total
                                                                                #print 'ivaret------>><',iva_ret
                                                                            #print "---->",iva_ret
                                                                        elif taxm.tax_category_id.id == 5:
                                                                            isr_ret = monto_total
                                                                            #print isr_ret
                                                                            #print iva_hon
                                                                        elif taxm.tax_category_id.id == 6:
                                                                            ieps = monto_total
                                                                            #print ieps
                                                                        elif taxm.tax_category_id.id == 3:
                                                                            iva_excento=monto_total
                                                                            excento=line.amount
                                                                            #print '4444',iva_excento
                                                                        elif taxm.tax_category_id.id == 9:
                                                                            iva_cero=monto_total
                                                                            #print iva_cero
                                                                        #print 'ant------>>>>>>>>>>',iva,'---',iva_ret
                                                            #print '#####',bantax
                                                            if not bantax == True:
                                                                excento=line.amount
                                                            else:
                                                                subtotal_grav = iva+gravado
                                                                subtotal_final = line.amount-subtotal_grav
                                                                if not subtotal_final < 1:
                                                                    excento = subtotal_final
                                                                else:
                                                                    excento = 0.0
                                                        
                                                    #print 'ivaaaaa y retttt------->>>>',iva,iva_ret
                                                    #-----------------------------------------------------

                                                    # print "---->>>move_ac",move_ac.id

                                           #impuestos
                                            if not ban_pas:
                                                #print 'entre passssssss---------------------------'
                                                #print 'linea guia',line.id
                                                cr.execute("""
                                                select id,tax_id from account_voucher_line_tax
                                                where voucher_line_id='%s' ;
                                                    """ % line.id)
                                                cr_res = cr.fetchall()

                                                if cr_res:
                                                    for cr_ in cr_res:
                                                        #id_imp.append(cr_[0])
                                                        #print '=====>>>',cr_[0]

                                                        #----------------------------------
                                                        cr.execute("""
                                                        select credit,name from account_move_line
                                                        where tax_id='%s' and credit!=0 ;
                                                            """ % cr_[0])
                                                        cr_prub = cr.fetchall()
                                                        #print '--->',cr_prub
                                                        #time.sleep(4)
                                                        #-----------------------------------

                                                        if cr_prub:
                                                            for prub_cr in cr_prub:

                                                                account_cat_browse = tax_cat_obj.browse([cr_[1]])[0]
                                                               
                                                                if account_cat_browse.tax_diot == 'tax_16':
                                                                    if not bantax:
                                                                        iva = prub_cr[0]
                                                                        bantax=True
                                                                        gravado=iva/.16
                                                               
                                                                if account_cat_browse.tax_category_id.id == 1 and not 'HON' in prub_cr[1] and iva_ret==0:
                                                                    iva_ret = prub_cr[0]
                                                                    #print "-->>>",iva_ret
                                                                elif account_cat_browse.tax_category_id.id == 5 and isr_ret ==0:
                                                                    isr_ret = prub_cr[0]
                                                                elif 'HON' in prub_cr[1] or 'hon' in prub_cr[1] and iva_hon==0:
                                                                    iva_hon = prub_cr[0]
                                                                elif account_cat_browse.tax_category_id.id == 6 and ieps==0:
                                                                    ieps = prub_cr[0]
                                                                #print '===========>>>>>>',iva
                                                                #print '===========',iva_ret
                                                if not bantax == True:
                                                    excento=line.amount
                                                else:
                                                    subtotal_grav = iva+gravado
                                                    subtotal_final = line.amount-subtotal_grav
                                                    if not subtotal_final < 1:
                                                        excento = subtotal_final
                                                    else:
                                                        excento = 0.0


                                            fecha_rep=account.date[6:7]
                                            #print '------',str(fecha_rep)
                                            if str(fecha_rep) == '9':
                                                #print 'entreeeee'
                                                account_tax_search = account_tax_obj.search([('invoice_id','=',account_invoice_browse.id)])
                                                #print 'ivaa2',iva
                                                if account_tax_search:
                                                    account_tax_browse = account_tax_search
                                                    if not account.amount == 0.0:
                                                        for tax in account_tax_browse:
                                                            if tax.tax_id.id:
                                                                account_cat_browse = tax.tax_id
                                                                #print 'impuuuuu',account_cat_browse.tax_diot
                                                                if account_cat_browse.tax_diot == 'tax_16':
                                                                    iva = tax.amount
                                                                elif account_cat_browse.tax_category_id.id == 1 and not 'HON' in tax.name and iva_ret==0:
                                                                    iva_ret = tax.amount*-1
                                                                    #print "-->>>",iva_ret
                                                                elif account_cat_browse.tax_category_id.id == 5 and isr_ret ==0:
                                                                    isr_ret = tax.amount
                                                                elif 'HON' in tax.name or 'hon' in tax.name and iva_hon==0:
                                                                    iva_hon = tax.amount
                                                                elif account_cat_browse.tax_category_id.id == 6 and ieps==0:
                                                                    ieps = tax.amount
                                                if not bantax == True:
                                                    excento=line.amount
                                                else:
                                                    subtotal_grav = iva+gravado
                                                    subtotal_final = line.amount-subtotal_grav
                                                    if not subtotal_final < 1:
                                                        excento = subtotal_final
                                                    else:
                                                        excento = 0.0
                                            #--------------------------------------------
                                                    
                                            account_inline_search = account_invoice_line_obj.search([('invoice_id','=',account_invoice_browse.id)])
                                            if account_inline_search:
                                                account_inline_browse = account_inline_search
                                                for inline in account_inline_browse:

                                                    product_search = product_obj.search([('id','=',inline.product_id.id)])
                                                    if product_search:
                                                        product_browse = product_search[0]
                                                        if not account.amount == 0.0:
                                                            if product_browse.tms_category == 'freight':
                                                                fletes=fletes+inline.price_subtotal
                                                            else:
                                                                otros=otros+inline.price_subtotal

                                                # MODIFICACION FLETES------------>>>

                                                if not fletes == 0:
                                                    #print 'no fletes'
                                                    if not otros == 0:
                                                        #print 'no otros'
                                                        if not iva == 0.0:
                                                            #print 'no iva'
                                                            if not iva_ret == 0.0:
                                                             #   print 'no iva_ret'
                                                                fletes = iva_ret/.04
                                                                otros = (iva/.16)-fletes

                                                            else:
                                                                fletes = 0.0
                                                                fleteret=iva/.16
                                                                otros= 0.0

                                                    else:
                                                        #print 'else'
                                                        if not iva==0.0:
                                                            if not iva_ret == 0.0:
                                                                fletes=(iva_ret)/.04
                                                            else:
                                                                fletes = iva/.16

                                                else:
                                                    #print 'else2'
                                                    if not otros == 0:
                                                        if not iva == 0.0:
                                                            #if not iva_ret == 0.0:
                                                            #    otros = (line.amount-(iva-(iva_ret*-1)))
                                                            #else:
                                                            otros = iva/.16

                                            ajournal_search= account_journal_obj.search([('id','=',account.journal_id.id)])
                                            if ajournal_search:
                                                #print 'etreeee'
                                                ajournal_browse= ajournal_search[0]

                                            if ajournal_browse.currency.id == 3:
                                                currency_rate_search=res_currency_rate_obj.search([('currency_id','=',account_invoice_browse.currency_id.id),('name','=',account.date)])
                                                if currency_rate_search:
                                                    #print 'entreeeee'
                                                    currency_rate_browse = currency_rate_search[0]
                                                    ratem = currency_rate_browse.rate
                                                else:
                                                    #print 'aquiii'
                                                    ratem = account_invoice_browse.currency_id.rate

                                                rate=1/ratem

                                                total = round(rate*line.amount,2)

                                                monto_iva=round(rate*account.amount,2)#round(rate*monto_iva,2)
         
                                                fecha_rep=account.date[6:7]
                                                if str(fecha_rep) == '9':

                                                    iva= round(rate*iva,2)
                                                    iva_ret= round(rate*iva_ret,2)
                                                    total = round(rate*line.amount,2)
                                                    gravado = round(rate*gravado,2)
                                                    excento= round(rate*excento,2)
                                                    isr_ret= round(rate*isr_ret,2)
                                                    iva_hon=round(rate*iva_hon,2)
                                                    ieps=round(rate*ieps,2)
                                                    monto_iva=round(rate*account.amount,2)#round(rate*monto_iva,2)
                                                    iva_excento=round(rate*iva_excento,2)
                                                    iva_cero=round(rate*iva_cero,2)
                                                    fletes=round(rate*fletes,2)
                                                    otros=round(rate*otros,2)

                                            else:
                                                total=round(line.amount,2)
                                                monto_iva=round(account.amount,2)

                                            if account_invoice_browse.type == 'out_refund' or account_invoice_browse.type == 'in_refund':
                                                iva=iva*-1
                                                iva_ret=iva_ret*-1
                                                total=total*-1
                                                gravado=gravado*-1
                                                excento=excento*-1
                                                isr_ret=isr_ret*-1
                                                iva_hon=iva_hon*-1
                                                ieps=ieps*-1
                                                monto_iva=monto_iva*-1
                                                iva_excento=iva_excento*-1
                                                iva_cero=iva_cero*-1
                                                fletes=fletes*-1
                                                fleteret=fleteret*-1
                                                otros=otros*-1

                                            if report_type == 'payment':
                                                income_expenses_line = {
                                                    'tipo': report_type,
                                                    'rfc': partner_browse.vat,
                                                    'name': partner_browse.name,
                                                    'type_journal': journal_browse.name,
                                                    'name_journal': amove_browse.name,
                                                    'date_journal': amove_browse.date,
                                                    'date_voucher': account.date,
                                                    'bank': journal_browse.name,
                                                    'number_account': account_invoice_browse.number,
                                                    'folio_account': account_invoice_browse.supplier_invoice_number,
                                                    'iva': iva,
                                                    'iva_ret': iva_ret,
                                                    'total': total,
                                                    'count': accounta_browse.name,
                                                    'date_invoice': account_invoice_browse.date_invoice,
                                                    'gravado': gravado,
                                                    'exento': excento,
                                                    'isr_ret': isr_ret,
                                                    'iva_hon': iva_hon,
                                                    'ieps': ieps,
                                                    'monto_iva': monto_iva,
                                                    'iva_excento': iva_excento,
                                                    'iva_cero': iva_cero,
                
                                                }
                                                generate_ids.append(account_inc_exp_obj.create(income_expenses_line).id)
                                            else:
                                                income_expenses_line = {
                                                    'tipo': report_type,
                                                    'rfc': partner_browse.vat,
                                                    'name': partner_browse.name,
                                                    'type_journal': journal_browse.name,
                                                    'name_journal': amove_browse.name,
                                                    'date_journal': amove_browse.date,
                                                    'date_voucher': account.date,
                                                    'bank': journal_browse.name,
                                                    'number_account': account_invoice_browse.number,
                                                    'folio_account': account_invoice_browse.supplier_invoice_number,
                                                    'date_invoice': account_invoice_browse.date_invoice,
                                                    'flete': fletes,
                                                    'fleteret':fleteret,
                                                    'other': otros,
                                                    'iva': iva,
                                                    'iva_ret': iva_ret,
                                                    'total': total,
                                                    'monto_iva': monto_iva,
                                                    'iva_excento': iva_excento,
                                                    'iva_cero': iva_cero,
                                                }
                                                generate_ids.append(account_inc_exp_obj.create(income_expenses_line).id)
        print ("################### generate_ids >>>>>>>>>>> ",generate_ids)
        return True
# #---------------------------------
#         if report_type == 'payment':
#             #print generate_ids
#             if not generate_ids:
#                 raise osv.except_osv(_('Processing Error!'), _('No se encontro ningun registro con los datos ingresados') \
#                                     % ())
         
#             value = {
#                 'type': 'ir.actions.report.xml',
#                 'report_name': 'report_account_income_expenses_xls', ### DEBE CONTENER EL NOMBRE DEL REPORTE ESTABLECIDO EN EL VIEW DEL REPORTE
#                 'datas': {
#                             'model' : 'account.inc.exp', #### DEBE CONTENER EL MODELO ESTABLECIDO EN EL VIEW DEL REPORTE
#                             'ids'   : generate_ids, ###### IDS CON LA INFORMACION A IMPRIMIR
#                             }
#                         }
            
#             return value
#         elif report_type == 'receipt':
#             #print generate_ids
#             if not generate_ids:
#                 raise osv.except_osv(_('Processing Error!'), _('No se encontro ningun registro con los datos ingresados') \
#                                     % ())
#             value = {
#                 'type': 'ir.actions.report.xml',
#                 'report_name': 'report_account_income_xls', ### DEBE CONTENER EL NOMBRE DEL REPORTE ESTABLECIDO EN EL VIEW DEL REPORTE
#                 'datas': {
#                             'model' : 'account.inc.exp', #### DEBE CONTENER EL MODELO ESTABLECIDO EN EL VIEW DEL REPORTE
#                             'ids'   : generate_ids, ###### IDS CON LA INFORMACION A IMPRIMIR
#                             }
#                         }
            
#             return value
#-------------------------------------      

        #return True



class account_inc_exp(models.Model):
    _name = 'account.inc.exp'
    _description = 'Income and Expenses Report'

    tipo = fields.Char('Tipo de Reporte', size=160)
    rfc = fields.Char('RFC', size=160)
    name = fields.Char('Cliente', size=160)
    type_journal = fields.Char('Tipo de Poliza', size=160)
    name_journal = fields.Char('Poliza', size=160)
    date_journal = fields.Date('Fecha de Poliza')
    date_voucher = fields.Date('Fecha de Pago')
    bank = fields.Char('Banco', size=160)
    number_account = fields.Char('Numero de Factura', size=160)
    folio_account = fields.Char('Folio Factura', size=160)
    flete = fields.Char('Flete', size=160)
    fleteret = fields.Char('Flete s ret', size=160)
    other = fields.Char('Otros', size=160)
    iva = fields.Float('IVA')
    iva_ret = fields.Float('Iva Retenido')
    total = fields.Float('Total')

    count = fields.Char('Cuenta', size=160)
    date_invoice = fields.Date('Fecha de Factura')
    gravado = fields.Float('Gravado')
    exento = fields.Float('Exento')
    isr_ret = fields.Float('ISR')
    iva_hon = fields.Float('IVA HON')
    ieps = fields.Float('IEPS')
    monto_iva = fields.Float('Total Iva')
    iva_excento = fields.Float('Total Iva Excento')
    iva_cero = fields.Float('Total Tasa 0')
        