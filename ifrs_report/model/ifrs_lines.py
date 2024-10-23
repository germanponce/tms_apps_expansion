# -*- coding: utf-8 -*-

from openerp import models, fields, api
import logging
_logger = logging.getLogger(__name__)
import operator as op

LOGICAL_RESULT = [
    ('subtract', 'Izquierda - Derecha'),
    ('addition', 'Izquierda + Derecha'),
    ('lf', 'Izquierda'),
    ('rg', 'Derecha'),
    ('zr', 'Cero (0)'),
]
LOGICAL_OPERATIONS = [
    ('gt', '>'),
    ('ge', '>='),
    ('lt', '<'),
    ('le', '<='),
    ('eq', '='),
    ('ne', '<>'),
]


class IfrsLines(models.Model):

    _name = 'ifrs.lines'
    _description = 'ifrs.lines'
    _order = 'ifrs_id, sequence'

    def _get_sum_total(self, operand, number_month=None, one_per=False, bag=None):
        """ Calculates the sum of the line total_ids & operand_ids the current
        ifrs.line
        @param number_month: period to compute
        """
        context = self.env.context.copy()
        res = 0

        # If the report is two or twelve columns, will choose the field needed
        # to make the sum
        if context.get('whole_fy', False) or one_per:
            field_name = 'ytd'
        else:
            field_name = 'period_%s' % str(number_month)

        # It takes the sum of the total_ids & operand_ids
        for ttt in getattr(self, operand):
            res += bag[ttt.id].get(field_name, 0.0)
        return res

    
    def _get_sum_detail(self, number_month=None, data=None):
        """ Calculates the amount sum of the line type == 'detail'
        @param number_month: periodo a calcular
        """
        fy_obj = self.env['account.fiscalyear']
        period_obj = self.env['account.period']
        ctx = data or self.env.context.copy()
        res = 0.0

        if not ctx.get('fiscalyear', False):
            ctx['fiscalyear'] = fy_obj.find()

        fy_id = ctx['fiscalyear']
        
        if self.acc_val == 'init':
            #print "Saldo Inicial"
            if ctx.get('whole_fy', False):
                self._cr.execute("""select ap.id from account_period ap
                                    where ap.fiscalyear_id in (
                                    select fy.id from account_fiscalyear fy
                                    where fy.name < (select name from account_fiscalyear fy2
                                    where fy2.id=%s));""" % fy_id)
                xres = self._cr.fetchall()
                ctx['periods'] = [x3[0] for x3 in xres]
                ctx.pop('fiscalyear')
            else:
                self._cr.execute("""select ap.id from account_period ap
                                    where ap.name2 < (select ap2.name2 from account_period ap2 where ap2.id=%s);""" % ctx['period_to'])
                xres = self._cr.fetchall()
                ctx['periods'] = [x3[0] for x3 in xres]
                ctx.pop('fiscalyear')
        elif self.acc_val == 'var':
            #print "Saldo Mensual"
            if ctx.get('whole_fy', False):
                self._cr.execute("""select id from account_period where fiscalyear_id in (
                                        select id from account_fiscalyear where name <= (
                                        select name from account_fiscalyear where id=%s));""" % fy_id)
                xres = self._cr.fetchall()
                ctx['periods'] = [x3[0] for x3 in xres]
                ctx.pop('fiscalyear')
            else:
                ctx['periods'] = [ctx['period_to']]
        else:
            #print "Saldo Acumulado"
            # it is going to be from the fiscalyear's beginning
            if ctx.get('whole_fy', False):
                self._cr.execute("""select ap.id from account_period ap where 
                                    id <> (select coalesce(aps.id, 0) from account_period aps where aps.fiscalyear_id=%s and aps.special)
                                    and
                                    ap.fiscalyear_id in (
                                        select id from account_fiscalyear where name <= (
                                        select name from account_fiscalyear where id=%s));""" % (fy_id,fy_id))
                xres = self._cr.fetchall()
                ctx['periods'] = [x3[0] for x3 in xres]
                ctx.pop('fiscalyear')
            else:
                self._cr.execute("""select ap.id from account_period ap
                                    where ap.name2 <= (select ap2.name2 from account_period ap2 where ap2.id=%s);""" % ctx['period_to'])
                xres = self._cr.fetchall()
                ctx['periods'] = [x3[0] for x3 in xres]
                ctx.pop('fiscalyear')
                
        #print "ctx: ", ctx
        
        if self.type == 'detail':
            # Si es de tipo detail
            # If we have to only take into account a set of Journals
            ctx['journal_ids'] = [aj_brw.id for aj_brw in self.journal_ids]
            analytic = [an.id for an in self.analytic_ids]
            # Tomo los ids de las cuentas analiticas de las lineas
            if analytic:
                # Si habian cuentas analiticas en la linea, se guardan en el
                # context y se usan en algun metodo dentro del modulo de
                # account
                ctx['analytic'] = analytic

            # NOTE: This feature is not yet been implemented
            # ctx['partner_detail'] = ctx.get('partner_detail')

            # Refreshing record with new context
            brw = self.with_context(ctx).browse(self.id)
            for aa in brw.with_context(ctx).cons_ids:
                # Se hace la sumatoria de la columna balance, credito o debito.
                # Dependiendo de lo que se escoja en el wizard
                if brw.value == 'debit':
                    res += aa.debit
                elif brw.value == 'credit':
                    res += aa.credit
                else:
                    res += aa.balance
        return res

    
    def _get_logical_operation(self, brw, ilf, irg):
        def result(brw, ifn, ilf, irg):
            if getattr(brw, ifn) == 'subtract':
                res = ilf - irg
            elif getattr(brw, ifn) == 'addition':
                res = ilf + irg
            elif getattr(brw, ifn) == 'lf':
                res = ilf
            elif getattr(brw, ifn) == 'rg':
                res = irg
            elif getattr(brw, ifn) == 'zr':
                res = 0.0
            return res

        #context = self.env.context.copy()
        fnc = getattr(op, brw.logical_operation)

        if fnc(ilf, irg):
            res = result(brw, 'logical_true', ilf, irg)
        else:
            res = result(brw, 'logical_false', ilf, irg)
        return res

    def _get_grand_total(self, number_month=None, one_per=False, bag=None):
        """ Calculates the amount sum of the line type == 'total'
        @param number_month: periodo a calcular
        """
        fy_obj = self.env['account.fiscalyear']
        #context = self.env.context.copy()
        ctx = self.env.context.copy()
        res = 0.0

        if not ctx.get('fiscalyear'):
            ctx['fiscalyear'] = fy_obj.find()

        brw = self #.browse(cr, uid, ids)
        res = self.with_context(ctx)._get_sum_total('total_ids', number_month, one_per=one_per, bag=bag)

        if brw.operator in ('subtract', 'condition', 'percent', 'ratio',
                            'product'):
            so = self.with_context(ctx)._get_sum_total('operand_ids', number_month, one_per=one_per, bag=bag)
            if brw.operator == 'subtract':
                res -= so
            elif brw.operator == 'condition':
                res = self.with_context(ctx)._get_logical_operation(brw, res, so)
            elif brw.operator == 'percent':
                res = so != 0 and (100 * res / so) or 0.0
            elif brw.operator == 'ratio':
                res = so != 0 and (res / so) or 0.0
            elif brw.operator == 'product':
                res = res * so
        return res

    
    def _get_constant(self, number_month=None):
        """ Calculates the amount sum of the line of constant
        @param number_month: periodo a calcular
        """
        context = self.env.context.copy()
        ctx = self.env.context.copy()
        brw = self #.browse(cr, uid, ids, context=ctx)
        if brw.constant_type == 'constant':
            return brw.constant
        fy_obj = self.env['account.fiscalyear']
        period_obj = self.env['account.period']

        if not ctx.get('fiscalyear'):
            ctx['fiscalyear'] = fy_obj.find()

        if not ctx.get('period_from', False) and not ctx.get('period_to', False):
            if context.get('whole_fy', False):                
                ctx['period_from'] = period_obj.find_special_period(ctx['fiscalyear'])
            ctx['period_to'] = period_obj.search([('fiscalyear_id', '=', ctx['fiscalyear'])])[-1]

        if brw.constant_type == 'period_days':
            res = period_obj._get_period_days(ctx['period_from'], ctx['period_to'])
        elif brw.constant_type == 'fy_periods':
            res = fy_obj._get_fy_periods(ctx['fiscalyear'])
        elif brw.constant_type == 'fy_month':
            res = fy_obj._get_fy_month(ctx['fiscalyear'], ctx['period_to'])
        elif brw.constant_type == 'number_customer':
            res = self.with_context(ctx)._get_number_customer_portfolio(ctx['fiscalyear'], ctx['period_to'])
        return res

    
    def exchange(self, from_amount, to_currency_id, from_currency_id, exchange_date):
        context = self.env.context.copy()
        if from_currency_id == to_currency_id:
            return from_amount
        context['date'] = exchange_date
        return self.env['res.currency'].browse(from_currency_id).with_context(context).compute(to_currency_id, from_amount)

    
    def _get_amount_value(self, ifrs_line=None, period_info=None, fiscalyear=None, exchange_date=None, currency_wizard=None,
                                number_month=None, target_move=None, pdx=None, undefined=None,
                                two=None, one_per=False, bag=None, data=None):
        """ Returns the amount corresponding to the period of fiscal year
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        """
        context = data and data.copy() or {}
        # TODO: Current Company's Currency shall be used: the one on wizard
        from_currency_id = ifrs_line.ifrs_id.company_id.currency_id.id
        to_currency_id = currency_wizard
        if number_month:
            if two:
                context.update({'period_from': number_month, 'period_to': number_month})
            else:
                period_id = period_info[number_month][1]
                context.update({'period_from': period_id, 'period_to': period_id})
        else:
            context['whole_fy'] = True

        # NOTE: This feature is not yet been implemented
        # context['partner_detail'] = pdx
        context['fiscalyear'] = fiscalyear
        context['state'] = target_move
        
        if ifrs_line.type == 'detail':
            res = self.with_context(context)._get_sum_detail(number_month, data=context)
        elif ifrs_line.type == 'total':
            res = self.with_context(context)._get_grand_total(number_month, one_per=one_per, bag=bag)
        elif ifrs_line.type == 'constant':
            res = self.with_context(context)._get_constant(number_month)
        else:
            res = 0.0

        if ifrs_line.type == 'detail':
            res = self.with_context(context).exchange(res, to_currency_id, from_currency_id,exchange_date)
        return res

    
    def _get_dict_amount_with_operands(self, ifrs_line, period_info=None, fiscalyear=None,
                                        exchange_date=None, currency_wizard=None, number_month=None,
                                        target_move=None, pdx=None, undefined=None, two=None,
                                        one_per=False, bag=None, data=None):
        """
        Integrate operand_ids field in the calculation of the amounts for each
        line
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        """

        context = data
        direction = ifrs_line.inv_sign and -1.0 or 1.0

        res = {}
        for number_month in range(1, 13):
            field_name = 'period_{month}'.format(month=number_month)
            bag[ifrs_line.id][field_name] = self.with_context(context)._get_amount_value(ifrs_line, period_info, fiscalyear,
                                                exchange_date, currency_wizard, number_month, target_move, pdx,
                                                undefined, two, one_per=one_per, bag=bag, data=context) * direction
            res[number_month] = bag[ifrs_line.id][field_name]

        return res

    
    def _get_amount_with_operands(self, ifrs_l, period_info=None, fiscalyear=None,
                                    exchange_date=None, currency_wizard=None, number_month=None,
                                    target_move=None, pdx=None, undefined=None, two=None,
                                    one_per=False, bag=None, data=None):
        """
        Integrate operand_ids field in the calculation of the amounts for each
        line
        @param ifrs_line: linea a calcular monto
        @param period_info: informacion de los periodos del fiscal year
        @param fiscalyear: selected fiscal year
        @param exchange_date: date of change currency
        @param currency_wizard: currency in the report
        @param number_month: period number
        @param target_move: target move to consider
        """
        context = data.copy()
        if not number_month:
            context['whole_fy'] = True
        res = self._get_amount_value(ifrs_l, period_info, fiscalyear, exchange_date,
                                     currency_wizard, number_month, target_move, pdx, undefined, 
                                     two, one_per=one_per, bag=bag, data=context)

        res = ifrs_l.inv_sign and (-1.0 * res) or res
        bag[ifrs_l.id]['ytd'] = res
        return res

    
    def _get_number_customer_portfolio(self, fyr, period):
        ifrs_brw = self #.browse(self.id)
        company_id = ifrs_brw.ifrs_id.company_id.id
        if self._context.get('whole_fy', False):
            period_fy = [('period_id.fiscalyear_id', '=', fyr),('period_id.special', '=', False)]
        else:
            period_fy = [('period_id', '=', period)]
        invoice_obj = self.env['account.invoice']
        invoice_ids = invoice_obj.search([('type', '=', 'out_invoice'),
                                          ('state', 'in', ('open', 'paid',)),
                                          ('company_id', '=', company_id)] + period_fy)
        partner_number = set([inv.partner_id.id for inv in invoice_ids])
        return len(list(partner_number))

    
    @api.onchange('sequence')
    def onchange_sequence(self):
        self.priority = self.sequence

    @api.returns('self')
    def _get_default_help_bool(self):
        ctx = self.env.context.copy()
        return ctx.get('ifrs_help', True)

    ##########################################    
    @api.returns('self')
    def _default_employee_get(self):
        return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    
    ######################################
    
    @api.returns('self')
    def _get_default_sequence(self):
        res = 0
        ifrs_lines_ids = self.search([],order='id desc',limit=10)
        if ifrs_lines_ids:
            res = max(line.sequence for line in ifrs_lines_ids)
        return res + 10

    @api.onchange('operator')
    def onchange_type_without(self):
        if self.type == 'total' and self.operator == 'without':
            self.operand_ids = []
        return

    @api.multi
    def write(self, vals):
        res = super(IfrsLines, self).write(vals)
        for ifrs_line in self: #.env['ifrs.lines').browse(cr, uid, ids):
            if ifrs_line.type == 'total' and ifrs_line.operator == 'without':
                vals['operand_ids'] = [(6, 0, [])]
                super(IfrsLines, self).write(vals)
        return res

    
    help = fields.Boolean(string='Show Help', copy=False, related='ifrs_id.help',
                            default=_get_default_help_bool,
                            help='Allows you to show the help in the form')
    # Really!!! A repeated field with same functionality! This was done due
    # to the fact that web view everytime that sees sequence tries to allow
    # you to change the values and this feature here is undesirable.
    sequence = fields.Integer(string='Secuencia', default=_get_default_sequence,
                                help=('Indica el orden de la línea en el reporte. La secuencia '
                                      'debe se única e irrepetible'))
    priority = fields.Integer(string='Prioridad', default=_get_default_sequence, related='sequence',
                                help=('Indica el orden de la línea en el reporte. La secuencia '
                                      'debe se única e irrepetible'))
    name = fields.Char(string='Etiqueta de Línea', size=128, required=True, translate=True,
                        help=('Etiqueta de la línea en el reporte. Este nombre puede ser traducible en '
                              'caso de tenet varios idiomas disponibles'))
    type = fields.Selection([('abstract', 'Abstracta'),
                             ('detail', 'Detalle'),
                             ('constant', 'Constante'),
                             ('total', 'Total')],
                            string='Tipo', required=True, default='abstract',
                            help=('Tipo de Línea en el reporte:  \n-Abstracta(A),\n-Detalle(D), '
                                  '\n-Constante(C),\n-Total(T)'))
    constant = fields.Float(string='Valor Constante',
                            help=('Indique el valor de la constante a usar para el cálculo de otras líneas'),
                            readonly=False)
    constant_type = fields.Selection([('constant', 'Mi propia Constante'),
                                      ('period_days', 'Días del Periodo'),
                                      ('fy_periods', "Año Fiscal de los Periodos"),
                                      ('fy_month', "Año Fiscal del Mes"),
                                      ('number_customer', "Número de clientes* en portafolio")],
                                        string='Tipo de Constante', required=False)
    ifrs_id = fields.Many2one('ifrs.ifrs', string='IFRS',required=True)
    company_id = fields.Many2one('res.company', string='Compañía', related='ifrs_id.company_id', store=True)
    amount = fields.Float(string='Monto', readonly=True,
                            help=('Este campo será actualizado cuando se le de clic al botón en el formulario de la definición de IFRS'))
    cons_ids = fields.Many2many('account.account', 'ifrs_account_rel', 'ifrs_lines_id', 'account_id',
                                string='Cuentas Consolidadas', copy=False)
    journal_ids = fields.Many2many('account.journal', 'ifrs_journal_rel', 'ifrs_lines_id', 'journal_id',
                                    string='Diarios Contables', required=False, copy=False)
    analytic_ids = fields.Many2many('account.analytic.account', 'ifrs_analytic_rel', 'ifrs_lines_id',
                                    'analytic_id', string='Cuentas Analíticas Consolidadas', copy=False)
    parent_id = fields.Many2one('ifrs.lines', string='Padre', ondelete='set null',
                                domain=("[('ifrs_id','=',parent.id),('type','=','total'),('id','!=',id)]"))
    operand_ids = fields.Many2many('ifrs.lines', 'ifrs_operand_rel', 'ifrs_parent_id', 'ifrs_child_id',
                                    string='Segundo Operando')
    operator = fields.Selection([('subtract', 'Resta'),
                                 ('condition', 'Condicional'),
                                 ('percent', 'Porcentaje'),
                                 ('ratio', 'Ratio'),
                                 ('product', 'Producto'),
                                 ('without', 'Solo Primer Operando')],
                                string='Operador', required=False,
                                default='without',
                                help='Si lo deja en blanco no tomará en cuenta los Operandos')
    logical_operation = fields.Selection(LOGICAL_OPERATIONS, string='Operaciones Lógicas', required=False,
                                        help=('Seleccione el tipo de Operación Lógica a realizar con los Operandos (Izquierda y Derecha)'))
    logical_true = fields.Selection(LOGICAL_RESULT, string='Logical True', required=False,
                                    help=('Value to return in case Comparison is True'))
    logical_false = fields.Selection(LOGICAL_RESULT, string='Logical False', required=False,
                                    help=('Value to return in case Comparison is False'))
    comparison = fields.Selection([('subtract', 'Resta'),
                                   ('percent', 'Porcentaje'),
                                   ('ratio', 'Ratio'),
                                   ('without', 'Sin Comparación')],
                                    string='Hacer Comparación', required=False,
                                    default='without',
                                    help=('Hacer Comparación contra un periodo previo.\nEsto es, '
                                          'periodo X(n) menos periodo X(n-1)\Dejarlo en blanco no tiene ningún efecto'))
    
    acc_val = fields.Selection([('init', 'Saldo Inicial'),
                                ('var', 'Variación en Periodos'),
                                ('fy', 'Saldo Final')],
                                string='Valor Contable', required=False,
                                default='fy')
    
    value = fields.Selection([('debit', 'Debe'),
                              ('credit', 'Haber'),
                              ('balance', 'Balance')],
                                string='Valor Contable', required=False,
                                default='balance')
    
    total_ids = fields.Many2many('ifrs.lines', 'ifrs_lines_rel', 'parent_id', 'child_id',
                                 string='Primer Operando')
    inv_sign = fields.Boolean(string='Cambiar Signo', default=False, copy=True)
    invisible = fields.Boolean(string='Invisible', default=False, copy=True,
                                help='Define si la línea del reporte se imprime o no')
    comment = fields.Text(string='Comentarios')

    #_sql_constraints = [
    #    ('sequence_ifrs_id_unique', 'unique(sequence, ifrs_id)',
    #     'The sequence already have been set in another IFRS line')]

    
    def _get_level(self, lll, tree, level=1):
        """ Calcula los niveles de los ifrs.lines, tomando en cuenta que sera
        un mismo arbol para los campos total_ids y operand_ids.
        @param lll: objeto a un ifrs.lines
        @param level: Nivel actual de la recursion
        @param tree: Arbol de dependencias entre lineas construyendose
        """
        #context = self.env.context.copy()
        if not tree.get(level):
            tree[level] = {}
        # The search through level should be backwards from the deepest level
        # to the outmost level
        #levels = tree.keys()
        #levels.sort()
        levels = sorted(tree)        
        levels.reverse()
        xlevel = False
        for nnn in levels:
            xlevel = isinstance(tree[nnn].get(lll.id), (set)) and nnn or xlevel
        if not xlevel:
            tree[level][lll.id] = set()
        elif xlevel < level:
            tree[level][lll.id] = tree[xlevel][lll.id]
            del tree[xlevel][lll.id]
        else:  # xlevel >= level
            return True
        for jjj in set(lll.total_ids + lll.operand_ids):
            tree[level][lll.id].add(jjj.id)
            self._get_level(jjj, tree, level + 1)#, context=context)
        return True
