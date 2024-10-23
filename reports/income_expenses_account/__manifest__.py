# -*- coding: utf-8 -*-
{
    'name': 'Reporte Egresos e Ingresos',
    'version': '1.0',
    'category': 'account',
    'description': """
            Modulo para la generacion de Reporte de Ingresos y los Egresos
    """,
    'author': 'Gemma Hdez',
    'website': 'http://www.argil.mx',
    'depends': ['stock', 'account','purchase'],
    'data': [
      "income_expenses_view.xml",
      "security/ir.model.access.csv",
    ],
    'installable': True,
    'auto_install': False,
}
