from email.policy import default
from odoo import _, api, fields, models


class MovementSourceHistory(models.Model):
    _name = "xepelin.bank.statement.upload.history"
    _description = "Upload history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Name")
    date = fields.Datetime(default=fields.Datetime.now)
    type = fields.Selection(
        string="Type", selection=[("bci", "BCI"), ("santander", "Santander")]
    )
    filename = fields.Char("Filename")
    file = fields.Binary(string="File", attachment=False, required=True)
    total = fields.Integer(string="Total", default=0)
    imported = fields.Integer(string="Imported", default=0)
    omitted = fields.Integer(string="Omitted", default=0)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
