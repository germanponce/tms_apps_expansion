# -*- coding: utf-8 -*-
# © <2015> <Jarsa Sistemas S.A. de C.V.>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Boton Recalcular Retenciones en Liquidaciones",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, Alejandro Robles (Desarrollador jr.)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": """
    Este modulo Agrega un Boton llamado Recalcular Retenciones, en el modulo de Liquidaciones.
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
        'expense.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
