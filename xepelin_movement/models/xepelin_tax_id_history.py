from odoo import _, api, fields, models


class MovementTaxIdHistory(models.Model):
    _name = "xepelin.movement.tax.id.history"
    _description = "Tax ID history"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "business_name"
    _rec_name = "business_name"

    business_name = fields.Char(string="Business name", required=True)
    tax_id = fields.Char(string="Tax ID", required=True)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    @api.model
    def create(self, vals):
        if vals.get("business_name"):
            vals["business_name"] = vals["business_name"].strip().upper()
        if vals.get("tax_id"):
            vals["tax_id"] = vals["tax_id"].strip().upper()
        result = super(MovementTaxIdHistory, self).create(vals)
        return result

    def write(self, vals):
        if vals.get("business_name"):
            vals["business_name"] = vals["business_name"].strip().upper()
        if vals.get("tax_id"):
            vals["tax_id"] = vals["tax_id"].strip().upper()
        result = super(MovementTaxIdHistory, self).write(vals)
        return result
