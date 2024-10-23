# -*- encoding: utf-8 -*-

{
    "name"      : "TMS + IFRS",
    "version"   : "1.0",
    "author"    : "Argil Consulting",
    "category"  : "Account",
    "description": """
Este módulo agrega filtro por Vehículos en el Asistente para obtener el reporte de IFRS
    """,
    "website"   : "http://www.argil.mx",
    "license"   : "OEEL-1",
    "depends"   : ["ifrs_report",
                   "fleet_extension",
                  ],
    "data"      : [
                    "views/tms_ifrs_wizard_view.xml",
                    ],
    "installable" : True,
}
