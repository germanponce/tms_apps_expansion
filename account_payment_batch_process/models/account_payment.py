# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import time 
import logging
_logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def _create_payment_entry(self, amount):
        # print ("############# _create_payment_entry >>>> ")
        """ Create a journal entry corresponding to a payment, if the payment
            references invoice(s) they are reconciled.
            Return the journal entry.
        """
        context = self._context
        # print ("##### context >>>> ",context)
        cr = self.env.cr

        # If group data
        if 'group_data' in self._context:
            aml_obj = self.env['account.move.line'].with_context(
                check_move_validity=False)
            invoice_currency = False
            comp_currency = all(
                [
                    x.currency_id == self.invoice_ids[0].currency_id
                    for x in self.invoice_ids
                ])

            if self.invoice_ids and comp_currency:
                # If all the invoices selected share the same currency,
                # record the paiement in that currency too
                invoice_currency = self.invoice_ids[0].currency_id

            move_vals = self._get_move_vals()
            # print ("### move_vals >>>>> ", move_vals)
            move = self.env['account.move'].create(move_vals)
            p_id = str(self.partner_id.id)

            self._cr.execute("""
                    drop table if exists borrame_partidas;
                    create table borrame_partidas(
                        id int);
                    """)
            payment_amount = 0.0
            x = 1
            w = len(self._context.get('group_data')[p_id]['inv_val'])
            company_currency_id = self.company_id.currency_id.id

            facturas_pago_menos = {}
            facturas_pago_menos_keys = []
            if 'facturas_pago_menos' in context:
                facturas_pago_menos = context['facturas_pago_menos']
                facturas_pago_menos_keys = facturas_pago_menos.keys()
            for inv in self._context.get('group_data')[p_id]['inv_val']:
                pago_de_menos = False
                if int(inv) in facturas_pago_menos_keys:
                    pago_de_menos = context['pago_de_menos']

                # print ("#### INV >>>>>>>> ",inv)
                current_invoice = self.env['account.invoice'].browse(int(inv))
                writeoff_account_id_from_ctxt = False
                if 'writeoff_account_id' in context:
                    writeoff_account_id_from_ctxt = context['writeoff_account_id']
                inv_amount_residual = 0.0
                if current_invoice.residual:
                    inv_amount_residual = current_invoice.residual
                # print ("############ inv_amount_residual >>>> ",inv_amount_residual)
                _logger.info("Procesando factura %s de %s" % (x, w))
                x += 1
                amt = 0
                p_group = self._context.get('group_data')
                if 'is_customer' in self._context \
                        and self._context.get('is_customer'):
                    amt = -(p_group[p_id]['inv_val'][inv]['receiving_amt'])
                else:
                    amt = p_group[p_id]['inv_val'][inv]
                payment_difference_from_ctxt = 0.0
                if inv_amount_residual < amt:
                    payment_difference_from_ctxt = amt - inv_amount_residual

                # print ("############ writeoff_account_id_from_ctxt >>>> ",writeoff_account_id_from_ctxt)
                # print ("############ payment_difference_from_ctxt >>>> ",payment_difference_from_ctxt)

                # print ("### AMT >>>> ",amt)
                aml_ctx = aml_obj.with_context(date=self.payment_date)
                debit, credit, amount_currency, currency_id = \
                    self.with_context(date=self.payment_date)._compute_amount_fields_argil(
                        amt, self.currency_id,
                        self.company_id.currency_id)
                # debit, credit, amount_currency, currency_id = \
                #     aml_ctx.compute_amount_fields(
                #         amt, self.currency_id,
                #         self.company_id.currency_id,
                #         invoice_currency)
                # Write line corresponding to invoice payment
                counterpart_aml_dict = \
                    self._get_shared_move_line_vals(
                        debit, credit, amount_currency, move.id, False)
                
                ml_vals = self._get_counterpart_move_line_vals(current_invoice)
                counterpart_aml_dict.update(ml_vals)

                ## German ###
                user_type_id = False
                acc_id_aml = counterpart_aml_dict['account_id']

                cr.execute("""
                    select user_type_id from account_account where id=%s;
                    """, (acc_id_aml, )) 
                cr_res_user_typ = cr.fetchall()
                user_type_id = cr_res_user_typ[0][0] if cr_res_user_typ and cr_res_user_typ[0] else False

                credit_upt = 0.0
                debit_upt = 0.0
                # print ("### counterpart_aml_dict >>>> ",counterpart_aml_dict)
                if 'is_customer' in self._context \
                    and self._context.get('is_customer') == False:
                    # print ("### COMENZAMOS LA CONTRAPARTIDA DE PAGO DE MAS O MENOS >>>> ")   
                    # print ("##### pago_de_menos >>>>>>>> ",pago_de_menos)
                    # print ("##### facturas_pago_menos >>>>>>>> ",facturas_pago_menos)
                    if 'credit' in  counterpart_aml_dict:
                        credit_upt = counterpart_aml_dict['credit']
                        if credit_upt:
                            counterpart_aml_dict.update({'credit_cash_basis': credit_upt})
                    if 'debit' in counterpart_aml_dict:
                        # print("### DEBIT >>> ")
                        debit_upt = counterpart_aml_dict['debit']
                        # print ("############# inv >>>> ",inv)
                        # print ("############# int(inv) in facturas_pago_menos_keys >>>> ",int(inv) in facturas_pago_menos_keys)
                        if pago_de_menos and int(inv) in facturas_pago_menos_keys:
                            # print ("####### POR ESTE LADO >>>>>>> ")
                            payment_plus_from_ctxt = facturas_pago_menos[int(inv)]
                            # print ("######## >>>>>>>> ",payment_plus_from_ctxt)
                            if debit_upt:
                                counterpart_aml_dict.update({'debit_cash_basis': debit_upt})
                            debit_result = counterpart_aml_dict['debit'] + payment_plus_from_ctxt
                            if debit_result:
                                counterpart_aml_dict['debit'] = debit_result

                        else:
                            if debit_upt:
                                counterpart_aml_dict.update({'debit_cash_basis': debit_upt})
                            debit_result = counterpart_aml_dict['debit'] - payment_difference_from_ctxt
                            if debit_result:
                                counterpart_aml_dict['debit'] = debit_result

                else:
                    if 'credit' in  counterpart_aml_dict:
                        credit_upt = counterpart_aml_dict['credit']
                        if credit_upt:
                            counterpart_aml_dict.update({'credit_cash_basis': credit_upt})
                    if 'debit' in counterpart_aml_dict:
                        debit_upt = counterpart_aml_dict['debit']
                        if debit_upt:
                            counterpart_aml_dict.update({'debit_cash_basis': debit_upt})

                # print ("########## counterpart_aml_dict >>>>>>>> ",counterpart_aml_dict)
                balance_cash_basis = debit_upt - credit_upt
                counterpart_aml_dict.update({'balance_cash_basis': balance_cash_basis, 'balance': balance_cash_basis})

                counterpart_aml_dict.update({'currency_id': currency_id, 
                                             'date_maturity': move.date, 
                                             'date': self.payment_date, 
                                             'period_id': move.period_id.id,
                                             'company_id': move.company_id.id,
                                             'create_date': fields.Datetime.now(),
                                             'create_uid': self.env.user.id,
                                             'write_uid': self.env.user.id,
                                             'write_date': fields.Datetime.now(),
                                             'user_type_id': user_type_id,
                                             'company_currency_id': company_currency_id,
                                             })

                columns_query = str(tuple(counterpart_aml_dict.keys()))
                columns_query = columns_query.replace("'","")

                values_dict = counterpart_aml_dict.values()

                values_query = []

                for x in values_dict:
                    if type(x) != str:
                        values_query.append(str(x))
                    else:
                        values_query.append(x)

                values_query = tuple(values_query)
                values_query = str(values_query)
                values_query = values_query.replace('False','null')

                query_final = "insert into account_move_line "+columns_query+" values "+ values_query +" returning id;"
                query_final = query_final.replace("'null'","null")
                # Insertando #
                cr.execute(query_final)
                cr_res = cr.fetchall()
                counterpart_aml_id = cr_res[0][0]
                # counterpart_aml_id = aml_obj.with_context(check_move_validity=False).create(counterpart_aml_dict)
                self.env.cr.execute("""
                    insert into borrame_partidas (id) values (%s);
                    """,(counterpart_aml_id, ))
                # Monto para la Reclasificacion #
                payment_amount += debit+credit

                #############

                # currency_dict = {
                #     'currency_id': currency_id
                # }
                # counterpart_aml_dict.update(currency_dict)
                # counterpart_aml = aml_obj.create(counterpart_aml_dict)
                # Reconcile with the invoices and write off
                
                #### Pagando de Menos #####
                if 'is_customer' in self._context \
                        and self._context.get('is_customer') == False:
                    # print ("### COMENZAMOS LA CONTRAPARTIDA DE PAGO DE MAS >>>> ")

                    p_group = self._context.get('group_data')
                    handling = 'handling'
                    payment_difference = payment_difference_from_ctxt

                    writeoff_account_id = writeoff_account_id_from_ctxt

                    if pago_de_menos == True:
                        if int(inv) in facturas_pago_menos_keys:
                            payment_plus_from_ctxt = facturas_pago_menos[int(inv)]
                            if not writeoff_account_id_from_ctxt:
                                raise UserError("Ocurrio un error con la revision del saldo pendiente.")

                            writeoff_line = \
                                self._get_shared_move_line_vals(
                                    0, 0, 0, move.id, False)
                            # print ( "############## WRITEOFF LINE >>>>>>>>> ",writeoff_line )
                            # aml_ctx = self.with_context(date=self.payment_date)
                            credit_wo, debit_wo, \
                                amount_currency_wo, \
                                currency_id = self.with_context(date=self.payment_date)._compute_amount_fields_argil(
                                    payment_plus_from_ctxt,
                                    self.currency_id,
                                    self.company_id.currency_id )
                            # print ( "############## aml_ctx >>>>>>>>>>>>>>> ",aml_ctx )
                            batch_writeoff_text = ""
                            if 'batch_writeoff_text' in context:
                                batch_writeoff_text = context['batch_writeoff_text']

                            writeoff_line['name'] = batch_writeoff_text if batch_writeoff_text else 'Partida Ajuste de saldo'
                            writeoff_line['account_id'] = writeoff_account_id
                            writeoff_line['debit'] = debit_wo
                            writeoff_line['credit'] = credit_wo
                            writeoff_line['amount_currency'] = amount_currency_wo
                            writeoff_line['currency_id'] = currency_id
                            ### GERMAN ###
                            # print ("########### writeoff_line >>>>>>>>>>> ",writeoff_line)
                            ### Insertando la Partida por Query ####
                            user_type_id = False
                            acc_id_wrt = writeoff_account_id
                            cr.execute("""
                                select user_type_id from account_account where id=%s;
                                """, (acc_id_wrt, )) 
                            cr_res_user_wrt = cr.fetchall()
                            user_type_id = cr_res_user_wrt[0][0] if cr_res_user_wrt and cr_res_user_wrt[0] else False

                            credit_upt = 0.0
                            debit_upt = 0.0
                            if 'credit' in  writeoff_line:
                                credit_upt = writeoff_line['credit']
                                if credit_upt:
                                    writeoff_line.update({'debit_cash_basis': credit_upt})
                            if 'debit' in writeoff_line:
                                debit_upt = writeoff_line['debit']
                                if debit_upt:
                                    writeoff_line.update({'credit_cash_basis': debit_upt})
                            balance_cash_basis = debit_upt - credit_upt
                            writeoff_line.update({'balance_cash_basis': balance_cash_basis, 'balance': balance_cash_basis})

                            writeoff_line.update({'currency_id': currency_id, 
                                                         'date_maturity': move.date, 
                                                         'date': self.payment_date, 
                                                         'period_id': move.period_id.id,
                                                         'company_id': move.company_id.id,
                                                         'create_date': fields.Datetime.now(),
                                                         'create_uid': self.env.user.id,
                                                         'write_uid': self.env.user.id,
                                                         'write_date': fields.Datetime.now(),
                                                         'user_type_id': user_type_id,
                                                         'company_currency_id': company_currency_id,
                                                         })

                            columns_query_1_1 = str(tuple(writeoff_line.keys()))
                            columns_query_1_1 = columns_query_1_1.replace("'","")

                            values_dict_1_1 = writeoff_line.values()

                            values_query_1_1 = []

                            for x in values_dict_1_1:
                                if type(x) != str:
                                    values_query_1_1.append(str(x))
                                else:
                                    values_query_1_1.append(x)

                            values_query_1_1 = tuple(values_query_1_1)
                            values_query_1_1 = str(values_query_1_1)
                            values_query_1_1 = values_query_1_1.replace('False','null')

                            query_final_1_1 = "insert into account_move_line "+columns_query_1_1+" values "+ values_query_1_1 +" returning id;"
                            query_final_1_1 = query_final_1_1.replace("'null'","null")
                            # Insertando #
                            cr.execute(query_final_1_1)
                            cr_res_1_1 = cr.fetchall()
                            writeoff_aml_id = cr_res_1_1[0][0]

                            ##############
                            # writeoff_line = aml_obj.create(writeoff_line)
                            if counterpart_aml_dict['debit']:
                                counterpart_aml_dict['debit'] += credit_wo - debit_wo
                            if counterpart_aml_dict['credit']:
                                counterpart_aml_dict['credit'] += debit_wo - credit_wo
                            counterpart_aml_dict['amount_currency'] -= \
                                amount_currency_wo
                            # print ("### LLEGAMOS A ESTE PUNTO >>>>>>>>>>>>> ")

                    #### Pagando de Mas #####
                    if payment_difference_from_ctxt and pago_de_menos == False:
                        if not writeoff_account_id_from_ctxt:
                            raise UserError("Ocurrio un error con la revision del saldo pendiente.")

                        writeoff_line = \
                            self._get_shared_move_line_vals(
                                0, 0, 0, move.id, False)
                        # print ( "############## WRITEOFF LINE >>>>>>>>> ",writeoff_line )
                        # aml_ctx = self.with_context(date=self.payment_date)
                        debit_wo, credit_wo, \
                            amount_currency_wo, \
                            currency_id = self.with_context(date=self.payment_date)._compute_amount_fields_argil(
                                payment_difference,
                                self.currency_id,
                                self.company_id.currency_id )
                        # print ( "############## aml_ctx >>>>>>>>>>>>>>> ",aml_ctx )
                        batch_writeoff_text = ""
                        if 'batch_writeoff_text' in context:
                            batch_writeoff_text = context['batch_writeoff_text']

                        writeoff_line['name'] = batch_writeoff_text if batch_writeoff_text else 'Partida Ajuste de saldo'
                        writeoff_line['account_id'] = writeoff_account_id
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                        writeoff_line['amount_currency'] = amount_currency_wo
                        writeoff_line['currency_id'] = currency_id
                        ### GERMAN ###
                        # print ("########### writeoff_line >>>>>>>>>>> ",writeoff_line)
                        ### Insertando la Partida por Query ####
                        user_type_id = False
                        acc_id_wrt = writeoff_account_id
                        cr.execute("""
                            select user_type_id from account_account where id=%s;
                            """, (acc_id_wrt, )) 
                        cr_res_user_wrt = cr.fetchall()
                        user_type_id = cr_res_user_wrt[0][0] if cr_res_user_wrt and cr_res_user_wrt[0] else False

                        credit_upt = 0.0
                        debit_upt = 0.0
                        if 'credit' in  writeoff_line:
                            credit_upt = writeoff_line['credit']
                            if credit_upt:
                                writeoff_line.update({'debit_cash_basis': credit_upt})
                        if 'debit' in writeoff_line:
                            debit_upt = writeoff_line['debit']
                            if debit_upt:
                                writeoff_line.update({'credit_cash_basis': debit_upt})
                        balance_cash_basis = debit_upt - credit_upt
                        writeoff_line.update({'balance_cash_basis': balance_cash_basis, 'balance': balance_cash_basis})

                        writeoff_line.update({'currency_id': currency_id, 
                                                     'date_maturity': move.date, 
                                                     'date': self.payment_date, 
                                                     'period_id': move.period_id.id,
                                                     'company_id': move.company_id.id,
                                                     'create_date': fields.Datetime.now(),
                                                     'create_uid': self.env.user.id,
                                                     'write_uid': self.env.user.id,
                                                     'write_date': fields.Datetime.now(),
                                                     'user_type_id': user_type_id,
                                                     'company_currency_id': company_currency_id,
                                                     })

                        columns_query_1_1 = str(tuple(writeoff_line.keys()))
                        columns_query_1_1 = columns_query_1_1.replace("'","")

                        values_dict_1_1 = writeoff_line.values()

                        values_query_1_1 = []

                        for x in values_dict_1_1:
                            if type(x) != str:
                                values_query_1_1.append(str(x))
                            else:
                                values_query_1_1.append(x)

                        values_query_1_1 = tuple(values_query_1_1)
                        values_query_1_1 = str(values_query_1_1)
                        values_query_1_1 = values_query_1_1.replace('False','null')

                        query_final_1_1 = "insert into account_move_line "+columns_query_1_1+" values "+ values_query_1_1 +" returning id;"
                        query_final_1_1 = query_final_1_1.replace("'null'","null")
                        # Insertando #
                        cr.execute(query_final_1_1)
                        cr_res_1_1 = cr.fetchall()
                        writeoff_aml_id = cr_res_1_1[0][0]

                        ##############
                        # writeoff_line = aml_obj.create(writeoff_line)
                        if counterpart_aml_dict['debit']:
                            counterpart_aml_dict['debit'] += credit_wo - debit_wo
                        if counterpart_aml_dict['credit']:
                            counterpart_aml_dict['credit'] += debit_wo - credit_wo
                        counterpart_aml_dict['amount_currency'] -= \
                            amount_currency_wo
                        # print ("### LLEGAMOS A ESTE PUNTO >>>>>>>>>>>>> ")

                if 'is_customer' in self._context \
                        and self._context.get('is_customer'):
                    p_group = self._context.get('group_data')
                    handling = p_group[p_id]['inv_val'][inv]['handling']
                    payment_difference = \
                        p_group[p_id]['inv_val'][inv]['payment_difference']
                    writeoff_account_id = \
                        p_group[p_id]['inv_val'][inv]['writeoff_account_id']
                    if handling == 'reconcile' and payment_difference:
                        writeoff_line = \
                            self._get_shared_move_line_vals(
                                0, 0, 0, move.id, False)
                        # aml_ctx = self.with_context(date=self.payment_date)
                        debit_wo, credit_wo, \
                            amount_currency_wo, \
                            currency_id = self.with_context(date=self.payment_date)._compute_amount_fields_argil(
                                payment_difference,
                                self.currency_id,
                                self.company_id.currency_id,)
                        writeoff_line['name'] = _('Counterpart')
                        writeoff_line['account_id'] = writeoff_account_id
                        writeoff_line['debit'] = debit_wo
                        writeoff_line['credit'] = credit_wo
                        writeoff_line['amount_currency'] = amount_currency_wo
                        writeoff_line['currency_id'] = currency_id
                        ### GERMAN ###
                        # print "########### writeoff_line >>>>>>>>>>> ",writeoff_line
                        ### Insertando la Partida por Query ####
                        user_type_id = False
                        acc_id_wrt = writeoff_account_id
                        cr.execute("""
                            select user_type_id from account_account where id=%s;
                            """, (acc_id_wrt, )) 
                        cr_res_user_wrt = cr.fetchall()
                        user_type_id = cr_res_user_wrt[0][0] if cr_res_user_wrt and cr_res_user_wrt[0] else False

                        credit_upt = 0.0
                        debit_upt = 0.0
                        if 'credit' in  writeoff_line:
                            credit_upt = writeoff_line['credit']
                            if credit_upt:
                                writeoff_line.update({'credit_cash_basis': credit_upt})
                        if 'debit' in writeoff_line:
                            debit_upt = writeoff_line['debit']
                            if debit_upt:
                                writeoff_line.update({'debit_cash_basis': debit_upt})
                        balance_cash_basis = debit_upt - credit_upt
                        writeoff_line.update({'balance_cash_basis': balance_cash_basis, 'balance': balance_cash_basis})

                        writeoff_line.update({'currency_id': currency_id, 
                                                     'date_maturity': move.date, 
                                                     'date': self.payment_date, 
                                                     'period_id': move.period_id.id,
                                                     'company_id': move.company_id.id,
                                                     'create_date': fields.Datetime.now(),
                                                     'create_uid': self.env.user.id,
                                                     'write_uid': self.env.user.id,
                                                     'write_date': fields.Datetime.now(),
                                                     'user_type_id': user_type_id,
                                                     'company_currency_id': company_currency_id,
                                                     })

                        columns_query_1_1 = str(tuple(writeoff_line.keys()))
                        columns_query_1_1 = columns_query_1_1.replace("'","")

                        values_dict_1_1 = writeoff_line.values()

                        values_query_1_1 = []

                        for x in values_dict_1_1:
                            if type(x) != str:
                                values_query_1_1.append(str(x))
                            else:
                                values_query_1_1.append(x)

                        values_query_1_1 = tuple(values_query_1_1)
                        values_query_1_1 = str(values_query_1_1)
                        values_query_1_1 = values_query_1_1.replace('False','null')

                        query_final_1_1 = "insert into account_move_line "+columns_query_1_1+" values "+ values_query_1_1 +" returning id;"
                        query_final_1_1 = query_final_1_1.replace("'null'","null")
                        # Insertando #
                        cr.execute(query_final_1_1)
                        cr_res_1_1 = cr.fetchall()
                        writeoff_aml_id = cr_res_1_1[0][0]

                        ##############
                        # writeoff_line = aml_obj.create(writeoff_line)
                        if counterpart_aml_dict['debit']:
                            counterpart_aml_dict['debit'] += credit_wo - debit_wo
                        if counterpart_aml_dict['credit']:
                            counterpart_aml_dict['credit'] += debit_wo - credit_wo
                        counterpart_aml_dict['amount_currency'] -= \
                            amount_currency_wo

                ### GERMAN ###
                aml_br = aml_obj.browse(counterpart_aml_id)
                aml_br._amount_residual()
                current_invoice.register_payment(aml_br)
                ##############
                # current_invoice.register_payment(counterpart_aml)
                # Write counterpart lines
                if not self.currency_id != self.company_id.currency_id:
                    amount_currency = 0
                liquidity_aml_dict = \
                    self._get_shared_move_line_vals(
                        credit, debit, -amount_currency, move.id, False)
                p_liq_ml = self._get_liquidity_move_line_vals(-amount)
                liquidity_aml_dict.update(p_liq_ml)
                #### GERMAN ####
                ### Insertando la Partida por Query ####
                user_type_id = False
                acc_id_liq = liquidity_aml_dict['account_id']
                cr.execute("""
                    select user_type_id from account_account where id=%s;
                    """, (acc_id_liq, )) 
                cr_res_user_liq = cr.fetchall()
                user_type_id = cr_res_user_liq[0][0] if cr_res_user_liq and cr_res_user_liq[0] else False
                
                credit_upt = 0.0
                debit_upt = 0.0
                if 'credit' in  liquidity_aml_dict:
                    credit_upt = liquidity_aml_dict['credit']
                    if credit_upt:
                        liquidity_aml_dict.update({'credit_cash_basis': credit_upt})
                if 'debit' in liquidity_aml_dict:
                    debit_upt = liquidity_aml_dict['debit']
                    if debit_upt:
                        liquidity_aml_dict.update({'debit_cash_basis': debit_upt })
                balance_cash_basis = debit_upt - credit_upt
                liquidity_aml_dict.update({'balance_cash_basis': balance_cash_basis, 'balance': balance_cash_basis})

                liquidity_aml_dict.update({'currency_id': currency_id, 
                                             'date_maturity': move.date, 
                                             'date': self.payment_date, 
                                             'period_id': move.period_id.id,
                                             'company_id': move.company_id.id,
                                             'create_date': fields.Datetime.now(),
                                             'create_uid': self.env.user.id,
                                             'write_uid': self.env.user.id,
                                             'write_date': fields.Datetime.now(),
                                             'user_type_id': user_type_id,
                                             'company_currency_id': company_currency_id,
                                             })

                columns_query_2 = str(tuple(liquidity_aml_dict.keys()))
                columns_query_2 = columns_query_2.replace("'","")

                values_dict_2 = liquidity_aml_dict.values()

                values_query_2 = []

                for x in values_dict_2:
                    if type(x) != str:
                        values_query_2.append(str(x))
                    else:
                        values_query_2.append(x)

                values_query_2 = tuple(values_query_2)
                values_query_2 = str(values_query_2)
                values_query_2 = values_query_2.replace('False','null')

                query_final_2 = "insert into account_move_line "+columns_query_2+" values "+ values_query_2 +" returning id;"
                query_final_2 = query_final_2.replace("'null'","null")
                # Insertando #
                cr.execute(query_final_2)
                cr_res_2 = cr.fetchall()
                liquidity_aml_id = cr_res_2[0][0]
                ################
                # aml_obj.create(liquidity_aml_dict)
            #### GERMAN ####
            tax_lines_dict = self._get_tax_paid_basis_entries_batch(move, payment_amount)
            # raise UserError("#AQUI NOMAS")
            if tax_lines_dict:
                aml_obj = self.env['account.move.line']
                move.button_cancel()
                self.argil_create_move_line(move.id, tax_lines_dict)
                move.post()
            else:
                move.post()
            ################
            # move.post()
            # raise UserError("AQUI 001 >>> ")
            ### **** Solo para Belchez **** ####
            # cr.execute("""
            #     update account_payment set x_move_reference_id = %s where id= %s;
            #     """, (move.id, self.id ))
            ### Insercion Referencia de Pago ####
            # if move:
            #     cr.execute("""
            #         update account_move_line set ref = 'REF: '||%s||' '||ref
            #             where move_id = %s;
            #         """, (self.payment_reference, move.id, ))

            ### Ajustando los Partners y los Montos ###
            self.env.cr.execute("""
                update account_move set partner_id=%s where id=%s;
                """, (self.partner_id.id, move.id,))

            self.env.cr.execute("""
                update account_move set amount = (select sum(debit) from account_move_line where move_id=account_move.id)  where id=%s;
                """, (move.id, ))
            #####################################

            ##### Ajustando la referencia #####
            invoice_names = ""
            if 'invoice_names' in context:
                invoice_names = context['invoice_names']
                # print ("### INVOICE NAMES >>>> ",invoice_names)
                # print ("### MOVE >>>> ",move.id)
                if invoice_names:
                    cr.execute("""
                        update account_move_line set ref = %s where move_id= %s and ref is null;
                        """, (invoice_names, move.id,))

                if self.payment_reference:
                    payment_rf = self.payment_reference
                    cr.execute("""
                        update account_move_line set payment_reference = %s where move_id= %s;
                        """, (payment_rf, move.id,))

                    cr.execute("""
                        update account_move set payment_reference = %s where id= %s;
                        """, (payment_rf, move.id,))
            
            ##### El Nombre del Partner y el Monto #####
            cr.execute("""
                update account_move_line set partner_id = %s where move_id = %s;
                """, (self.partner_id.id, move.id))
            cr.execute("""
                update account_move set partner_id = %s where id = %s;
                """, (self.partner_id.id, move.id))
            cr.execute("""
                update account_move set amount = (select sum(credit) from account_move_line where move_id = account_move.id)
                where id = %s;
                """, (move.id, ))
            return move
        #raise UserError("AQUI 002 >>> ")
        return super(AccountPayment, self)._create_payment_entry(amount)


    @api.model
    def _compute_amount_fields_argil(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(company) if company else self.env.user.company_id
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            amount = src_currency._convert(amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id


    def _get_tax_paid_basis_entries_batch(self, move, payment_amount):
        """ Reconcile payable/receivable lines from the invoice with payment_line """
        if not self.invoice_ids:
            return []
        active_ids = self.invoice_ids.ids
        
        currency_obj = self.env['res.currency']
        invoice_obj = self.env['account.invoice']
        
        move_id = move.id
        company_currency_id = self.company_id.currency_id
        payment_currency_id = self.currency_id or company_currency_id
        
        # payment_amount_company_curr = self.move_line_ids[0].debit + self.move_line_ids[0].credit
        #### GERMAN ####
        payment_amount_company_curr = payment_amount
        ################
        payment_amount_original_curr = self.amount
        invoice_currency_id = self.invoice_ids[0].currency_id
        currency_flag = False
        if company_currency_id.id == payment_currency_id.id == invoice_currency_id.id: # Invoice(s) & Payment in Company Currency
            payment_amount = payment_amount_company_curr
            currency_flag = True
        elif company_currency_id.id != payment_currency_id.id and payment_currency_id.id == invoice_currency_id.id: # Same Currency for Payment & Invoice(s) but not in company Currency
            payment_amount = payment_amount_original_curr
        else: # Payment, Invoice(s) and Company Currency not equal from each other            
            payment_amount = payment_currency_id.with_context(date=self.payment_date).compute(payment_amount_original_curr, invoice_currency_id)
        invoice_ids = active_ids #[x.id for x in self.invoice_ids]
        invoices_grouped = {}
        try:
            #### GERMAN #####
            cr_res = []
            self.env.cr.execute("""
                select id from borrame_partidas;
                """)
            partidas_res = self.env.cr.fetchall()
            partidas_ids = [x[0] for x in partidas_res]
            for partida in partidas_ids:
                self._cr.execute("""
                        drop table if exists borrame_partidas;
                        select aml.id
                        into borrame_partidas
                        from account_move_line aml
                        inner join account_account aa on aa.id=aml.account_id and aa.internal_type in ('payable', 'receivable')
                        where payment_id=%s;
                        select ai.id, apr.amount, apr.amount_currency, apr.currency_id, aml.date_maturity
                        from account_partial_reconcile apr
                        inner join account_move_line aml on aml.id <>  %s
                                                            and (aml.id=apr.credit_move_id or aml.id=apr.debit_move_id)
                        inner join account_invoice ai on ai.move_id=aml.move_id
                        where (apr.credit_move_id=%s or 
                               apr.debit_move_id=%s)
                        order by aml.date_maturity asc;
                    """ % (self.id, partida, partida, partida))
                consulta_cr = self._cr.fetchall()
                if consulta_cr:
                    for rs in consulta_cr:
                        cr_res.append(rs)
                ################
        except:
            raise ValidationError(_("Advertencia !\nLa cuenta contable del Diario de Pago no está configurada correctamente, debe ser Tipo Bancos / Caja"))
        
        # cr_res = self._cr.fetchall()
        sum_voucher_lines = 0.0
        for x in cr_res:
            
            val = {}
            val['invoice_id'], val['invoice_amount'], val['invoice_amount_currency'], val['invoice_currency_id'] = x[0], abs(x[1]), abs(x[2]), x[3]
            if not payment_amount:
                continue
            if payment_amount >= (currency_flag and val['invoice_amount'] or val['invoice_amount_currency']):
                val['amount_assigned'] = (currency_flag and val['invoice_amount'] or val['invoice_amount_currency'])
                payment_amount = payment_amount - (currency_flag and val['invoice_amount'] or val['invoice_amount_currency'])
            elif payment_amount and payment_amount < (currency_flag and val['invoice_amount'] or val['invoice_amount_currency']):
                val['amount_assigned'] = payment_amount
                payment_amount = 0.0
            else:
                val['amount_assigned'] = 0.0
            key = (val['invoice_id'],val['invoice_currency_id'])
            sum_voucher_lines += val['invoice_amount']
            if not key in invoices_grouped:
                invoices_grouped[key] = val
            else:
                invoices_grouped[key]['invoice_amount'] += val['invoice_amount']
                invoices_grouped[key]['invoice_amount_currency'] += val['invoice_amount_currency']
                invoices_grouped[key]['amount_assigned'] += val['amount_assigned']
            
        precision = self.env['decimal.precision'].precision_get('Account')
        journal_id = self.journal_id.id
        date = self.payment_date
        currency_obj = self.env['res.currency']
        res = []

        for inv in invoices_grouped.values():
            factor_base = sum_voucher_lines and inv['invoice_amount'] / sum_voucher_lines or 0.0

            for invoice in invoice_obj.browse([inv['invoice_id']]):
                factor = inv['amount_assigned'] / invoice.amount_total

                for inv_line_tax in invoice.tax_line_ids.filtered(lambda r: r.tax_id.use_tax_cash_basis==True):
                    #_logger.info("\n------------------------------\nImpuesto: %s" % inv_line_tax.tax_id.name)
                    src_account_id = inv_line_tax.tax_id.account_id.id
                    dest_account_id = inv_line_tax.tax_id.tax_cash_basis_account.id
                    if not (src_account_id and dest_account_id):
                        raise UserError(_("Tax %s is not properly configured, please check." % (inv_line_tax.tax_id.name)))
                    mib_company_curr_orig, mi_company_curr_orig = 0.0, 0.0
                    for move_line in invoice.move_id.line_ids:
                        if move_line.account_id.id == inv_line_tax.tax_id.account_id.id and \
                            move_line.tax_id_secondary.id == inv_line_tax.tax_id.id:
                            mi_company_curr_orig = (move_line.debit + move_line.credit) * factor
                            mib_company_curr_orig = move_line.amount_base * factor
                    if not mib_company_curr_orig and not inv_line_tax.tax_id.amount:
                        mib_company_curr_orig = inv_line_tax.amount_base_company_curr
                    #mi_invoice = inv_line_tax.amount * factor
                    #mib_invoice = mib_company_curr_orig / (mi_company_curr_orig / mi_invoice)                    
                    #################################
                    if ((invoice.type=='out_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                                 (invoice.type=='in_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                        debit = round(abs(mi_company_curr_orig),2) or 0.0
                        credit = 0.0
                        #amount_currency = (company_currency_id.id != invoice.currency_id.id) and abs(mi_invoice) or False
                    elif ((invoice.type=='in_invoice' and inv_line_tax.tax_id.amount >= 0.0) or \
                                 (invoice.type=='out_invoice' and inv_line_tax.tax_id.amount < 0.0)):
                        debit = 0.0
                        credit = round(mi_company_curr_orig,2) or 0.0
                        #amount_currency = (company_currency_id.id != invoice.currency_id.id) and -abs(mi_invoice) or False
                    #################################
                    line2 = {
                            'name'            : inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'quantity'        : 1,
                            'product_uom_id'  : False,
                            'partner_id'      : invoice.partner_id.id, 
                            'debit'           : debit,
                            'credit'          : credit,
                            'account_id'      : src_account_id, 
                            'journal_id'      : journal_id,
                            'period_id'       : move.period_id.id,
                            'company_id'      : invoice.company_id.id,
                            'move_id'         : move.id,
                            'tax_id_secondary': inv_line_tax.tax_id.id,
                            'analytic_account_id': False,
                            'date'            : date,
                            'date_maturity'   : date,
                            'amount_base'     : mib_company_curr_orig,
                            'payment_id'      : self.id,
                        }
                    #_logger.info("line2: %s" % line2)
                    line1 = line2.copy()
                    line3 = {}
                    xparam = self.env['ir.config_parameter'].get_param('tax_amount_according_to_currency_exchange_on_payment_date')[0]
                    if not xparam == "1" or (company_currency_id.id == payment_currency_id.id == invoice.currency_id.id):
                        line1.update({
                            'name': inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'account_id'  : dest_account_id,
                            'debit'       : line2['credit'],
                            'credit'      : line2['debit'],
                            'amount_base' : line2['amount_base'],
                            #'amount_currency' : line2['amount_currency'] and -line2['amount_currency'] or False,
                            })
                    elif xparam == "1":
                        
                        xfactor = float(inv_line_tax.amount_base / invoice.amount_total)
                        monto_base = round(factor_base * (\
                                            (inv_line_tax.tax_id.amount and (payment_amount_company_curr * xfactor)) \
                                                          or inv_line_tax.amount_base_company_curr), 2) 

                        monto_a_reclasificar = round(inv_line_tax.tax_id.amount and monto_base * (inv_line_tax.tax_id.amount / 100) or 0.0,2)
                        
                        
                        line1.update({
                            'name': inv_line_tax.tax_id.name + ((_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                            'debit': line2['credit'] and abs(monto_a_reclasificar) or 0.0,
                            'credit': line2['debit'] and abs(monto_a_reclasificar) or 0.0,
                            'account_id': dest_account_id,
                            'amount_base' : abs(monto_base),
                            })
                        #_logger.info("line1: %s" % line1)
                        
                        if (round(mi_company_curr_orig, 2) - round(monto_a_reclasificar,2)):
                            amount_diff =  (round(abs(mi_company_curr_orig),2) - round(abs(monto_a_reclasificar),2)) * \
                                            (inv_line_tax.tax_id.amount >= 0 and 1.0 or -1.0)
                            amount_diff = round(amount_diff,2)
                            line3 = {
                                'name': _('Diferencia de ') + inv_line_tax.tax_id.name + (invoice and (_(" - Fact: ") + (invoice.type=='out_invoice' and invoice.number or invoice.reference)) or 'N/A'),
                                'quantity': 1,
                                'partner_id': invoice.partner_id.id,
                                'debit': ((amount_diff < 0 and invoice.type=='out_invoice') or (amount_diff >= 0 and invoice.type=='in_invoice')) and abs(amount_diff) or 0.0,
                                'credit': ((amount_diff < 0 and invoice.type=='in_invoice') or (amount_diff >= 0 and invoice.type=='out_invoice')) and abs(amount_diff) or 0.0,
                                'account_id': (amount_diff < 0 ) and inv_line_tax.tax_id.tax_cash_basis_account_diff_credit.id or inv_line_tax.tax_id.tax_cash_basis_account_diff_debit.id,
                                'journal_id': journal_id,
                                'period_id': move.period_id.id,
                                'company_id': invoice.company_id.id,
                                'move_id': move.id,
                                'analytic_account_id': False,
                                'date': date,
                                'date_maturity'   : date,
                                'currency_id': False,
                                'amount_currency' : False,
                                'payment_id'      : self.id,
                                }
                        else:
                            line3 = {}
                        #_logger.info("line3: %s" % line3)
                    lines = line3 and [(0,0,line1),(0,0,line2),(0,0,line3)] or [(0,0,line1),(0,0,line2)]
                    res += lines
                #for resx in res:
                #    _logger.info("resx: %s" % resx)
                #raise UserError('Pausa...')
        return res


########## Agrupando Las Partidas #######################

    @api.multi
    def group_moves_data_in_payment(self):
        for rec in self:
            destination_account_id = rec.destination_account_id.id
            destination_journal_id = rec.destination_journal_id.id
            account_journal_id = rec.payment_type in ('outbound','transfer') and rec.journal_id.default_debit_account_id.id or rec.journal_id.default_credit_account_id.id
            if not account_journal_id:
                _logger.info("\n:::::: Error al Agrupar. No se pudo obtener la cuenta del diario %s " % rec.destination_journal_id.name)
                return True

            if rec.invoice_ids:
                invoices = rec.invoice_ids
                invoice_ids_reconciled = self.env['account.invoice']
                invoice_ids_from_moves = self.env['account.invoice']
                account_move_line_invoice_reconciled = self.env['account.move.line']
                account_move_line_obj = self.env['account.move.line']
                move_ids = self.env['account.move']
                ### Agrupamos la Cuenta Destino del Pago ###
                account_move_lines_groupped_credit = []
                account_move_lines_groupped_debit = []
                finally_amount_groupped_credit = 0.0
                finally_amount_groupped_debit = 0.0
                finally_amount_currency_credit = 0.0
                finally_amount_currency_debit = 0.0
                if rec.move_line_ids:
                    for line in rec.move_line_ids:
                        if line.account_id.id == account_journal_id:
                            if line.credit:
                                account_move_lines_groupped_credit.append(line)                     
                                finally_amount_groupped_credit += line.credit 
                                if line.amount_currency:
                                    finally_amount_currency_credit += line.amount_currency
                            else:
                                account_move_lines_groupped_debit.append(line)                     
                                finally_amount_groupped_debit += line.debit
                                if line.amount_currency:
                                    finally_amount_currency_debit += line.amount_currency
                        if not line.move_id in move_ids:
                            move_ids += line.move_id
                if not account_move_lines_groupped_credit and not account_move_lines_groupped_debit:
                    _logger.info("\n:::: No hay nada que agrupar >>> ")
                    return True
                _logger.info("\n:::: finally_amount_currency_credit >>> %s " % finally_amount_currency_credit)
                _logger.info("\n:::: finally_amount_currency_debit >>> %s " % finally_amount_currency_debit)

                len_credit_grouped = len(account_move_lines_groupped_credit)
                line_credit_grouped_first = account_move_lines_groupped_credit[0] if account_move_lines_groupped_credit else False
                len_debit_grouped = len(account_move_lines_groupped_debit)
                line_debit_grouped_first = account_move_lines_groupped_debit[0] if account_move_lines_groupped_debit else False
                ### configuramos las partidas a eliminar sin la linea 0 ###
                if account_move_lines_groupped_credit:
                    account_move_lines_groupped_credit.pop(0)
                if account_move_lines_groupped_debit:
                    account_move_lines_groupped_debit.pop(0)
                group_something = False
                if len_credit_grouped > 1:
                    group_something = True
                if len_debit_grouped > 1:
                    group_something = True
                if not group_something:
                    _logger.info("\n:::: No hay nada que agrupar >>> ")
                    return True
                ### CANCELAMOS LOS APUNTES CONTABLES ###
                for mv in move_ids:
                    if mv.state != 'draft':
                        mv.button_cancel()

                ### AQUI CONTINUAMOS CON LA ELIMINACION DE LAS PARTIDAS ####
                for cdel in account_move_lines_groupped_credit:
                    cdel.with_context(unlink_force_from_payment_group=True).unlink()
                for ddel in account_move_lines_groupped_debit:
                    ddel.with_context(unlink_force_from_payment_group=True).unlink()
                ### Ajustamos los Montos a la primer Partida ####
                if line_credit_grouped_first:
                    line_credit_grouped_first.write({'credit':finally_amount_groupped_credit})
                    if finally_amount_currency_credit:
                        line_credit_grouped_first.write({'amount_currency':finally_amount_currency_credit})
                if line_debit_grouped_first:
                    line_debit_grouped_first.write({'debit':finally_amount_groupped_debit})
                    if finally_amount_currency_debit:
                        line_debit_grouped_first.write({'amount_currency':finally_amount_currency_debit})
                # mv_f_id = move_ids[0]
                # mv_f_id.line_ids.unlink()
                ### VOLVEMOS A CONCILIAR ###
                for mv in move_ids:
                    if mv.state in ('cancel','draft'):
                        mv.post()


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit ='account.move'

    payment_reference = fields.Char('Referencia del Pago', size=256)


    @api.multi
    def _post_validate(self):
        context = self._context
        if 'unlink_force_from_payment_group' in context and context['unlink_force_from_payment_group']:
            return True
        else:
            return super(AccountMove, self)._post_validate()
            
class AccountMoveLine(models.Model):
    _name = 'account.move.line'
    _inherit ='account.move.line'
    
    payment_reference = fields.Char('Referencia del Pago', size=256)
