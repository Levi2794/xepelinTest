# -*- coding: utf-8 -*-

{
    "name": "Xepelin Movements",
    "version": "15.0.0.1",
    "summary": "Movements",
    "description": "Reconciliation of bank movements with order invoices",
    "category": "Xepelin/Accounting",
    "author": "C&C",
    "website": "https://xepelin.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "account",
        "account_accountant",
        "account_bank_statement_import",
        "l10n_mx",
        "l10n_mx_edi",
        "xepelin_order"
    ],
    "data": [
        #"security/ir.model.access.csv",
        "data/partner_bank.xml",
        "data/journals.xml",
        "wizards/account_bank_statement_import.xml",
        "views/account_journal.xml",
        "views/account_bank_statement_view.xml"
    ],
    "assets": {
        'web.assets_qweb': [
            'xepelin_movements/static/src/xml/**/*',
        ],
    },
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
