# -*- encoding: utf-8 -*-
# Coded by German Ponce Dominguez 
#     ▬▬▬▬▬.◙.▬▬▬▬▬  
#       ▂▄▄▓▄▄▂  
#    ◢◤█▀▀████▄▄▄▄▄▄ ◢◤  
#    █▄ █ █▄ ███▀▀▀▀▀▀▀ ╬  
#    ◥ █████ ◤  
#     ══╩══╩═  
#       ╬═╬  
#       ╬═╬ Dream big and start with something small!!!  
#       ╬═╬  
#       ╬═╬ You can do it!  
#       ╬═╬   Let's go...
#    ☻/ ╬═╬   
#   /▌  ╬═╬   
#   / \
# Cherman Seingalt - german.ponce@outlook.com

{
    "name": "Carta Porte - Validaciónes en el complemento Carta Porte",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """

Validaciones Carta Porte.


    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "tms",
        "l10n_mx_einvoice",
        "l10n_mx_einvoice_waybill_complemento_ce",
        "l10n_mx_einvoice_waybill_complemento_tms",
        "fleet_extension",
    ],
    "data": [
        # 'reports/report_invoice_mx.xml',
        'account_view.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
