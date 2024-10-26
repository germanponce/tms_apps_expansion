# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Extensión de Acuerdos de Compra y Albaranes",
    "version": "12.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, <German Ponce Dominguez>",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """

Agrega la sucursal en los apuntes contables.

    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "sale",
        "purchase_requisition",
        "purchase",
        "tms",
        "stock",
        "stock_account",
        "fleet_mro",
        "multi_store_purchase",
        "fleet_extension",
        "l10n_mx_einvoice",
        "asti_eaccounting_mx_base"
    ],
    "data": [
        # 'tms_xml.xml'
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
