# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Batch Payments integracion con TMS",
    "summary": "Process Payments in Batch",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Argil Consulting & German Ponce",
    "category": "Generic Modules/Payment",
    "website": "https://argil.mx",
    "description" : """

Batch Muti Pagos - TMS
======================

Esta Aplicacion permite registrar multiples pagos para:
    - Anticipos
    - Liquidaciones

Debemos correr el siguiente Query despues de Instalar:

update tms_expense set handling = 'reconcile' where paid=True;

update tms_advance set handling = 'reconcile' where paid=True;


""",
    "depends": [
        "account",
        "account_check_printing",
        "l10n_mx_einvoice",
        "argil_account_tax_cash_basis",
        "account_payment_batch_process",
        "tms",
        "fleet_mro",
    ],
    "data": [
        "payment_reference.xml",
        "wizard/advance_batch_process_view.xml",
        "wizard/expense_batch_process_view.xml",
        "advance_views.xml",
        "expense_views.xml",
        "security/ir.model.access.csv",

    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["cherman.seingalt"],
}
