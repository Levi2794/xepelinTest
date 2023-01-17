from odoo import _, api, fields, models


class MovementDiscount(models.Model):
    _name = "xepelin.bank.statement.discount"
    _description = "Order Discounts"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    reason = fields.Char(string="Reason")
    external_id = fields.Char(string="Ext id")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    amount = fields.Monetary(string="Amount")
    order_id = fields.Many2one(
        comodel_name="xepelin.bank.statement.order", string="Order"
    )
