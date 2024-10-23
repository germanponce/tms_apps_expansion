# -*- encoding: utf-8 -*-
###########################################################################
#
#    Copyright (c) 2015 Argil Consulting - http://www.argil.mx
#    All Rights Reserved.
############################################################################

{
    "name": "Factura con Addenda Pemex",
    "version": "1.0",
    "depends": [
        'account',
        "l10n_mx_einvoice_addenda_no_sale",
        "l10n_mx_einvoice"
    ],
    "author": "Gernmn Ponce",
    "description" : """


Debemos ingresar el campo llamado Supplier Number  dentro del Cliente, ya que sera tomado para la generación de la Addenda.

En los Albaranes debemos ingresar el campo Id Recepcion solo para clientes Pepsico, dentro de la pestaña Información Adicional.

    """,
    "website": "http://www.argil.mx",
    "category": "Accounting",
    "demo": [],
    "test": [],
    "data" : [
                'views/account_cfdi_view.xml',
             ],
    'application': False,
    #"active": False,
    "installable": True,
}
