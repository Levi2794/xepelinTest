from odoo import fields,models

class XepelinPaymentRequestMaxPerCurrency(models.Model):
  _name = 'xepelinpaymentrequest.maxpercurrency'
  _description = 'Max per currency'

  currency_id = fields.Many2one('res.currency', string="Currency", required=True)
  amount = fields.Float('Amount', required=True)
