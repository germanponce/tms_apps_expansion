# -*- coding: utf-8 -*-
{
    'name': "ARCHIVOS Y VIGENCIAS RH",

    'summary': """
        Nos permite agregar algunas funcionalidades y campos dentro del proceso de selección.""",

    'description': """
        Nos permite agregar algunas funcionalidades y campos dentro del proceso de selección.
    """,

    'author': "German Ponce Dominguez, Argil Consulting",
    'email': 'german.ponce@outlook.com',
    'website': "https://argil.mx",
    'category': 'Extras',
    'version': '1.2',

    'depends': ['base','hr','hr_recruitment','tms','fleet_extension'],
    'data': [
            # 'security/.xml',
            'security/ir.model.access.csv',
            'views/hr.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'qweb': [
    ],
}