# -*- coding: utf-8 -*-

from odoo import fields, models


class OrderDiscount(models.Model):
    _name = "xepelin.order.discount"
    _description = "Order Discounts"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    reason = fields.Char(string="Reason")
    external_id = fields.Char(string="Ext. id")
    company_id = fields.Many2one("res.company", string="Company", ondelete='restrict', default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency",string="Currency", ondelete='restrict', default=lambda self: self.env.user.company_id.currency_id.id,)
    amount = fields.Monetary(string="Amount")
    order_id = fields.Many2one("xepelin.order", string="Order", ondelete='restrict')
