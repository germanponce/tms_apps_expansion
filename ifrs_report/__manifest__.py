# -*- coding: utf-8 -*-

{
    "name": "IFRS",
    "version": "1.0",
    "author" : "Argil",
    "category": "Accounting",
    "website": "http://www.argil.mx",
    #'license' : 'OEEL-1',
    "depends": [
        "account",
        "l10n_mx_account_tree",
        "account_period_and_fiscalyear",
    ],
    "demo": [],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "view/wizard.xml",
        "view/ifrs_view.xml",
        #"report/layouts.xml",
        "report/template.xml",
        #"data/report_paperformat.xml",
        "view/report.xml",
        "data/data_ifrs.xml",
    ],
    "test": [],
    "js": [],
    "css": [],
    "qweb": [],
    "installable": True,
    "application": True,
}
