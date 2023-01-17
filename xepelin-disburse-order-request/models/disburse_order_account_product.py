from pickle import TRUE
from odoo import fields,models

class XepelinDisburseOrderAccountProduct(models.Model):
    _name = 'xepelindisburseorder.disburse_order_account_product'
    _description = 'Disburse Order Request Account per Product'

    account_number = fields.Char(string='Account number', required=True)
    product = fields.Char(
        selection=[
            ('DIRECT_FINANCING', 'Financiamiento Directo'),
            ('EARLY_PAYMENT', 'Pronto Pago'),
            ('CONFIRMING', 'Payment')
        ],
        string='Product',       
        required=True
    )

    country = fields.Many2one('res.country', string="Country", required=False)

