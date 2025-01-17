# -*- coding: utf-8 -*-
{
    'name': "Descuento en Monto para Ventas",

    'summary': """
        Adds option to set float discount value for order, sale""",

    'description': """
        In addition to the percentage discount, you can now add its value directly. It's simple, fast and easy.
        Works for lines in quotations, orders, invoices and vendor bills.
    """,

    "website": "http://argil.mx",

    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '12.0.1.0.0',
    'license': 'LGPL-3',
    'support': 'german.ponce@argil.mx',
    'images': ['images/main_screenshot.png'],

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}