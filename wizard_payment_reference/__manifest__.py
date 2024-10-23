# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Ref. Pago en Asistente de Pagos",
    "summary": "Nos permite registrar un campo extra como Ref. al realizar Pagos.",
    "version": "12.0.1.0.0",
    "license": "AGPL-3",
    "author": "German Ponce",
    "category": "Generic Modules/Payment",
    "website": "https://poncesoft.blogspot.com",
    "depends": [
        "account",
    ],
    "data": [
        "wizard/invoice_batch_process_view.xml",
        "wizard/payment_reference.xml",
    ],
    "application": False,
    "development_status": "Beta",
    "maintainers": ["cherman.seingalt"],
}
