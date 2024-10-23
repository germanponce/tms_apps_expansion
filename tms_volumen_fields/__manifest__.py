# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "TMS - Modificaciones en Cartas Porte",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """
CAMPOS - VOLUMEN Y TEMPERATURA
==============================

Crea 4 campos en cartas porte para la linea de productos transportados después de peso:

  - Volumen de Carga

  - Volumen de descarga

  - Temperatura de carga

  - Temperatura de descarga

Agrega el Campo Volumen Total debajo del Total de la Carta Porte.


    """,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "account",
        "tms",
        
    ],
    "data": [
        # 'reports/report_invoice_mx.xml',
        'tms_view.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
