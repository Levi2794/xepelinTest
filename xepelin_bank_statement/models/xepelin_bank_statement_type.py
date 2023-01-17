from odoo import _, api, fields, models


class MovementPaymentType(models.Model):
    _name = "xepelin.bank.statement.type"
    _description = "Payment types"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(string="Name", required=True, tracking=True)
    color = fields.Integer(string="Color", required=True, tracking=True)
    description = fields.Html(string="Description", required=True)
    reconcile = fields.Boolean(string="Can reconcile?")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
