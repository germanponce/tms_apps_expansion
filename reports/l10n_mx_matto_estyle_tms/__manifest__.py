# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Reporte MATTO",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, Alejandro Robles (Desarrollador jr.)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": "MATTO",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "tms",
        
    ],
    "data": [
        'reports/report_invoice_mx.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
