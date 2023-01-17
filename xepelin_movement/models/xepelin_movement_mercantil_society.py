from odoo import _, api, fields, models


class MovementMercantilSociety(models.Model):
    _name = "xepelin.movement.mercantil.society"
    _description = "Mercantil societies"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "name"

    name = fields.Char(string="Name")
    description = fields.Text(string="Description")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
