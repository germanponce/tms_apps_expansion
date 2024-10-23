# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Cotizaciones - Fecha de Validez General",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """
Fecha Vencimiento Cotizaciones
==============================

Es modulo agrega un campo dentro de la configuración de ventas llamado:
    - Fecha Validez

Elimina la generación por medio del plazo en dias por uno general, el cual debera ser alimentado de acuerdo a lo que se requiera.

    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "sale",
        
    ],
    "data": [
        # 'reports/report_invoice_mx.xml',
        'sale_view.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
