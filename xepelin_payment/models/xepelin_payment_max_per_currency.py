# -*- coding: utf-8 -*-

from odoo import fields,models


class PaymentMaxPerCurrency(models.Model):
    _name = 'xepelin.payment.max.per.currency'
    _description = 'Max per currency'

    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    amount = fields.Float('Amount', required=True)
