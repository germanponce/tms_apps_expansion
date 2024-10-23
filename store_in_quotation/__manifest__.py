# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Cotizaciones - Sucursal en Presupuestos",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """
Sucursal en Presupuestos
========================

Es modulo agrega un campo dentro de las cotizaciones el campo llamado:
    - Sucursal


Este campo permitira identificar de que sucursal se genero la cotización, asi mismo podras agruparlas dentro de los presupuestos y pedidos de venta.

    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "sale",
        "sale_stock",
        "stock",
        "multi_store_base"
        
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
