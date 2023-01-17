# -*- coding: utf-8 -*-

{
    "name": "Xepelin Movements",
    "version": "15.0.0.1",
    "summary": "Movements",
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
        "security/xepelin_movement_security.xml",
        "data/sequences.xml",
        "views/xepelin_movement_movement_views.xml",
        "views/xepelin_movement_order_views.xml",
        "views/xepelin_movement_invoice_views.xml",
        "views/xepelin_movement_rsm_views.xml",
        "views/xepelin_movement_spei_views.xml",
        "views/xepelin_movement_cfdi_views.xml",
        "views/xepelin_movement_bnc_views.xml",
        "views/xepelin_movement_upload_history_views.xml",
        "views/xepelin_movement_payment_type_views.xml",
        "views/xepelin_movement_tax_id_history_views.xml",
        "views/xepelin_movement_discount_views.xml",
        "views/xepelin_movement_mercantil_society_views.xml",
        "views/res_company_views.xml",
        "wizards/res_config_settings.xml",
        "wizards/import_source_movement.xml",
        "views/menus.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "xepelin_movement/static/src/js/import_tree_button.js",
        ],
        "web.assets_qweb": [
            "xepelin_movement/static/src/xml/import_tree_button.xml",
        ],
    },
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
