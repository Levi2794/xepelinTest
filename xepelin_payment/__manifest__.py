# -*- coding: utf-8 -*-

{
    'name': 'Xepelin Payments',
    'version': '15.0.0.1',
    'summary': 'Payments',
    'description': 'Module to request payments to suppliers',
    'category': 'Xepelin/Accounting',
    'author': 'Xepelin',
    'website': 'https://xepelin.com/mx',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/res_currency.xml',
        'data/xepelin_payment_banks.xml',
        'data/xepelin_payment_config.xml',
        'data/xepelin_payment_max_per_currency.xml',
        'data/xepelin_payment_area.xml',
        'data/res_user.xml',
        'views/xepelin_payment_payment_views.xml',
        'views/menus.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
