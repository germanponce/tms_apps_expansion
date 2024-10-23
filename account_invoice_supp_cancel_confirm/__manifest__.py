# -*- encoding: utf-8 -*-

{
    'name': 'Confirmación de Cancelacion de Factura de Proveedor',
    'version': '1',
    "author" : "Argil Consulting",
    "category" : "Account",
    'description': """

Solicita el motivo de la Cancelacion asi como una Confirmacion.

    """,
    "website" : "http://www.argil.mx",
    'license' : 'OEEL-1',
    "depends" : ["account_cancel",
                 "account"],
    "data" : [
              'views/account_invoice_view.xml',
              'security/ir.model.access.csv',
                    ],
    "installable" : True,
}
