from odoo import fields,models

class Bank(models.Model):
  _name = 'xepelinpaymentrequest.bank'
  _description = 'Bank'

  name = fields.Char(string='Name')
  code = fields.Char(string='Code')
  country_id = fields.Many2one('res.country', string="Country", required=True)
