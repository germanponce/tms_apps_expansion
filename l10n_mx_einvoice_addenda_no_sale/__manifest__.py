# -*- encoding: utf-8 -*-

{
    "name"      : "Addendas para Facturas Electrónicas (CFDI)",
    "version"   : "1.0",
    "author"    : "Argil Consulting",
    "website"   : "https://www.argil.mx",
    "category"  : "Localization/Mexico",
    "license"   : "OEEL-1",
    "description" : """
    
    ADDENDAS para la Localizaci&oacute; Mexicana
    
    """,    
    "depends"   : ["l10n_mx_einvoice",
                   "account_invoice_resend_email",
                  ],
    "data"      : ["views/res_partner_view.xml",
                   "views/account_invoice_view.xml",
                   #"views/account_payment_view.xml",
                  ],
    "installable" : True,
}
