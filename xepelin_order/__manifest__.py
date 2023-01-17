# -*- coding: utf-8 -*-

{
    "name": "Xepelin Orders",
    "version": "15.0.0.1",
    "summary": "Orders",
    "category": "Xepelin/Sales",
    "author": "C&C",
    "website": "https://xepelin.com",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "account",
        "product",
        "xepelin_api_servers"
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "data/products.xml",
        "wizards/search_orderinvoice.xml",
        "views/xepelin_order_discount.xml",
        "views/xepelin_order.xml",
        "views/menus.xml"
    ],
    "assets": {},
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
