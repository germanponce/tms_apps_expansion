# -*- coding: utf-8 -*-
# © <2015> <German Ponce Dominguez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Reportes Electronicos para Viajes - TMS",
    "version": "11.0.1.0.0",
    "category": "Report",
    "website": "http://argil.mx",
    "author": "<Argil Consulting S.A. de C.V.>, German Ponce Dominguez (Desarrollador)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "description": "Bitacoras de Viaje",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "sale",
        "account",
        "tms",
        "tms",
    ],
    "data": [
        'security/ir.model.access.csv',
        'reports/report_bitacora_1.xml',
        'reports/report_bitacora_2.xml',
        'view/models_view.xml',
        'data/data.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
