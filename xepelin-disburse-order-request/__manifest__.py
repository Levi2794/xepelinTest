# -*- coding: utf-8 -*-

{
    'name': 'Xepelin Disburse Order Request',
    'version': '1.0',
    'summary': 'Disburse Order Request',
    'description': 'Module to request disburse order to suppliers',
    'category': 'Xepelin / Accounting',
    'author': 'Xepelin',
    'website': 'https://xepelin.com/mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'data': [
        'data/disburse_order_account_product.xml',
        'security/ir.model.access.csv',
        'views/xepelin_disburse_order_payment_request_views.xml',
        'views/menus.xml',
        'wizards/res_config_settings.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
