# -*- encoding: utf-8 -*-

{
    'name': 'Registro de Diff Cuenta en Pago de Anticipos',
    'version': '1',
    "author" : "Argil Consulting",
    "category" : "Account",
    'description': """


Enviar la Diferencia de mas de un Anticipo a cuenta X.

    """,
    "website" : "http://www.argil.mx",
    'license' : 'OEEL-1',
    "depends" : ["tms",
                 "account",
                 "hr", 
                 "stock", 
                 "fleet_extension"
                 ],
    "data" : [
              'views/account_invoice_view.xml',
              # 'security/ir.model.access.csv',
                    ],
    "installable" : True,
}
