# -*- coding: utf-8 -*-

{
    "name": "Modificaciones para Carta Porte",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez (Desarrollador Odoo)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": "Agrega algunas modificaciones de datos y restricciones para el modulo TMS",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "tms",
        "l10n_mx_einvoice",
        "l10n_mx_einvoice_waybill_complemento_ce",
        
    ],
    "data": [
        #'reports/report_invoice_mx.xml',
        'tms_view.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
