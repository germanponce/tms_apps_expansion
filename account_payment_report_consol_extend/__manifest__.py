# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Batch Payments Processing",
    "summary": "Process Payments in Batch",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "Argil Consulting & German Ponce",
    "category": "Generic Modules/Payment",
    "website": "https://argil.mx",
    "depends": [
        "account",
        "account_check_printing",
        "l10n_mx_einvoice",
        "argil_account_tax_cash_basis",
        "account_payment_batch_process",
    ],
    "data": [
        "views/invoice_view.xml",
    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["cherman.seingalt"],
}
