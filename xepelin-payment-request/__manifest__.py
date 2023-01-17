# -*- coding: utf-8 -*-

{
    'name': 'Xepelin Payment Request',
    'version': '1.0',
    'summary': 'Payment Request',
    'description': 'Module to request payments to suppliers',
    'category': 'Xepelin / Accounting',
    'author': 'Xepelin',
    'website': 'https://xepelin.com/mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'data/res_currency.xml',
        'data/payment_request_config.xml',
        'data/payment_request_max_per_currency.xml',
        'data/payment_request_bank.xml',
        'security/xepelin_payment_request_security.xml',
        'security/ir.model.access.csv',
        'views/xepelin_payment_request_payment_request_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
