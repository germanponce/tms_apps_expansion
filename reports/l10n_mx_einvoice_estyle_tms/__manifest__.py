# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Reporte Electronico CFDI 3.3 (Estilo Carta Porte)",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez (Desarrollador)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": "Factura Electronica Estilo TMS",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "l10n_mx_einvoice",
        "l10n_mx_einvoice_cedula_fiscal",
    ],
    "data": [
        'reports/report_invoice_mx.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
