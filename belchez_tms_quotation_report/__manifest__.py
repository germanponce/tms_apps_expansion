# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Reporte  Cotizacion para Belchez",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": "Reporte Personalizado para Cotizaciones Belchez",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "sale",
        "float_number_discount",
        
    ],
    "data": [
        'reports/quotation_report.xml',
        'mail_template.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
