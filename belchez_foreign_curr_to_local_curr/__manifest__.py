# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Argil Consulting (<http://www.argil.mx>)
#    Information:
#    Israel Cruz Argil  - israel.cruz@argil.mx
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################

{   
    "name"        : "Dólares a Pesos en Varias Pantallas",
    "version"     : "1",
    "category"    : "Account",
    'complexity'  : "easy",
    "author"      : "Argil Consulting",
    "website"     : "http://www.argil.mx",
    "depends"     : ["account","tms","tms_analysis_extend"],
    "summary"     : "Dólares a Pesos en Varias Pantallas",
    "description" : """
Dólares a Pesos en Varias Pantallas
===================================

CARTAS PORTE: 

- Nueva columna en Listado de Cartas Porte mostrando el SUBTOTAL en MXN


ANALISIS DE VIAJE:

- Se agrega una columna en la vista de lista para mostrar el Monto en MXN
- Se agrega una columna para mostrar la Moneda registrada en el Viaje
- Se agrega una agrupación por la columna Moneda


ANALISIS DE CARTAS PORTE:

- Se agrega una columna en la vista de lista para mostrar el Monto en MXN
- Se agrega una columna para mostrar la Moneda registrada en el Viaje
- Se agrega una agrupación por la columna Moneda


FACTURA DE CLIENTES:

- En la vista de lista se agrega una columna para el monto en MXN.
- Se agrega agrupación por moneda

PAGOS DE CLIENTES / A PROVEEDORES:

- En la vista de lista se agrega una columna para el monto en MXN.
- Se agrega agrupación por moneda

""",

    "data" : [
        'account_invoice_view.xml',
        'account_voucher_view.xml',
        'tms_waybill_view.xml',
        ],
    "application": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
