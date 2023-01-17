# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MovementSpei(models.Model):
    _name = "xepelin.movement.spei"
    _description = "SPEI Movements"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _sql_constraints = [
        ("spei_rsm_unique", "unique (rsm_id)", "The RSM can only be linked once"),
    ]
    _order = "date asc"

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    account_number = fields.Char(string="Account", tracking=True, required=True)
    date = fields.Datetime(string="Date", required=False)
    numerical_reference = fields.Char(
        string="Numerical reference", tracking=True, copy=False, required=True
    )
    legend_code_concept = fields.Char(
        string="Legend code concept", tracking=True, required=True
    )
    reference = fields.Char(string="Reference", required=True, copy=False)
    concept = fields.Char(string="Concept", required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    balance = fields.Monetary(string="Balance", tracking=True)
    payer_bank = fields.Char(string="Payer bank", required=False)
    payer_name = fields.Char(string="Payer name", required=False)
    payer_account = fields.Char(string="Payer account", required=False)
    beneficiary_name = fields.Char(string="Beneficiary name", required=False)
    beneficiary_bank = fields.Char(string="Beneficiary bank", required=False)
    beneficiary_account = fields.Char(string="Beneficiary account", required=True)
    tracking_key = fields.Char(string="Tracking key", required=False)
    payment_status = fields.Char(string="Payment status", required=False)
    return_reason = fields.Char(string="Return reason", required=False)
    state = fields.Selection(
        selection=[
            ("pending_merge", "Pending merge"),
            ("merged", "Merged"),
        ],
        string="State",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="pending_merge",
    )
    imported = fields.Boolean(default=False)
    import_date = fields.Date(string="Import date")
    rsm_id = fields.Many2one(
        comodel_name="xepelin.movement.rsm",
        string="RSM Movement",
        domain="[('state', '=', 'pending_merge')]",
    )
    upload_history_id = fields.Many2one(
        comodel_name="xepelin.movement.upload.history", string="Upload History"
    )

    @api.constrains("date", "numerical_reference", "amount", "tracking_key", "balance")
    def _check_unique(self):
        for record in self:
            spei_movement = self.search_count(
                [
                    ("account_number", "=", record.account_number),
                    ("date", "=", record.date),
                    ("numerical_reference", "=", record.numerical_reference),
                    ("amount", "=", record.amount),
                    ("tracking_key", "=", record.tracking_key),
                    ("balance", "=", record.balance),
                ]
            )
            if spei_movement > 1:
                raise ValidationError(
                    _(
                        "An record already exists with the same "
                        "date, numerical reference, amount, tracking key and balance."
                    )
                )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.spei"
            ) or _("New")
        res = super(MovementSpei, self).create(vals)
        return res

    def write(self, values):
        result = super(MovementSpei, self).write(values)
        return result

    def action_merge(self):
        if self.rsm_id and self.state == "pending_merge":
            self.write({"state": "merged"})
            self.rsm_id.write({"state": "merged", "spei_id": self.id})
