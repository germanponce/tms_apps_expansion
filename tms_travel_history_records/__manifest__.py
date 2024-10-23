# -*- coding: utf-8 -*-
# © <2015> <German Ponce Dominguez>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Historial de Monitoreo - TMS",
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
        'view/models_view.xml',
        'reports/report_monitoring_1.xml',
        # 'data/data.xml',
    ],
    "demo": [
    ],
    "qweb": [
    ]
}
