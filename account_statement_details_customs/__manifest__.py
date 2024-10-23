# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 German Ponce Dominguez
#
##############################################################################

{
    'name' : 'Reporte de Seguimiento de Clientes',
    'category': 'Sales',
    'version': '1.0',
    'author': 'Argil Consulting, German Ponce Dominguez',
    'website': 'https://argil.mx',
    'description': """
         Reporte de Seguimiento de Clientes

    """,
    'summary': 'Este modulo modifica la información de Estado de Cuenta.',
    'depends' : ['base', 'account_reports_followup', 'account_reports', 'account', 'tms'],
    'price': 500,
    'currency': 'USD',
    'license': 'OPL-1',
    'data': [
        # 'views/data.xml',
        # 'views/account.xml',
        # "security/ir.model.access.csv",
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: