# -*- encoding: utf-8 -*-
###########################################################################
#    Module Writen to German Ponce Dominguez :D
#    info skype: german_442 email: (german.ponce@argil.mx)
############################################################################
#    Coded by: german_442 email: (german.ponce@argil.mx)
##############################################################################

{
    'name': 'Generacion de Polizas de Cancelacion (Cartas Porte)',
    'version': '1',
    "author" : "Argil Consulting/German Ponce Dominguez",
    "category" : "Account",
    'description': """
Descripcion
===========
    - Este modulo adapta una metodologia basada en Polizas, para poder Cancelar movimientos sin eliminar las Polizas, todo esto mediante la creacion de movimientos inversos, creando una poliza que fue nombrada Poliza de Cancelacion.

USO
===
    - Este modulo trabaja de la siguiente Forma:
        - Genera una Poliza Inversa (Poliza de Cancelacion), con la fecha seleccionada en el Asistente de Cancelacion, el campo tiene por nombre 'Fecha de Poliza Cancelacion'.
        - La Poliza anterior es rehubicada en el campo Poliza Cancelada.
        - Concilia las Polizas Anteriores.
        - Al Confirmar genera la nueva Poliza en el periodo de acuerdo a la fecha seleccionada.

    """,
    "website" : "http://www.argil.mx/",
    "license" : "AGPL-3",
    "depends" : ["account","tms","account_invoice_cancel"],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'tms.xml',
                    ],
    "installable" : True,
    "active" : False,
}
