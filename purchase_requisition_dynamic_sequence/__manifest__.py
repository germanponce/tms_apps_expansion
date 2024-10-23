# -*- coding: utf-8 -*-
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
    "name": "Secuencias Dinamicas para Acuerdos de Compra",
    "version": "12.0.1.0.0",
    "category": "Purchases",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, <German Ponce Dominguez>",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """

Agrega un Estado de Acuerdo en las requisiciones de Compra para tener Secuencias Dinamicas.

    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "purchase_requisition",
        "purchase",
        "hr",
        
    ],
    "data": [
        'data.xml',
        'purchase_view.xml',
    ],
    "post_init_hook": "post_init_hook",
}
