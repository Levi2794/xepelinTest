# -*- coding: utf-8 -*-

{
    "name": "Xepelin Bank Statement",
    "version": "15.0.0.1",
    "summary": "Bank statements",
    "description": "Reconciliation of bank movements with order invoices",
    "category": "Xepelin/Accounting",
    "author": "C&A",
    "website": "https://xepelin.com/mx",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequences.xml",
        "data/res_company_data.xml",
        "views/xepelin_bank_statement_views.xml",
        "views/xepelin_bank_bci_views.xml",
        "views/xepelin_bank_santander_views.xml",
        "views/xepelin_bank_statement_order_views.xml",
        "views/xepelin_bank_statement_invoice_views.xml",
        "views/xepelin_bank_statement_upload_history_views.xml",
        "views/xepelin_bank_statement_type_views.xml",
        "wizards/import_bank_statement.xml",
        "wizards/res_config_settings.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "xepelin_bank_statement/static/src/js/import_tree_button.js",
        ],
        "web.assets_qweb": [
            "xepelin_bank_statement/static/src/xml/import_tree_button.xml",
        ],
    },
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
