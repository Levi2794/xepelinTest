from pickle import TRUE
from odoo import fields,models

class XepelinPaymentRequestConfig(models.Model):
    _name = 'xepelinpaymentrequest.config'
    _description = 'Payment resquest configuration'

    name = fields.Char(string='Configuration name')
    value = fields.Char(string='Configuration value')

    _sql_constraints = [(
        'unique_name',
        'UNIQUE(name)',
        "There can only be one configuration with that name."
    )]