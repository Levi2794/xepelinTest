# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MovementBnc(models.Model):
    _name = "xepelin.movement.bnc"
    _description = "BNC Movements"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _sql_constraints = [
        ("bnc_rsm_unique", "unique (rsm_id)", "The RSM can only be linked once"),
    ]
    _order = "payment_date asc"

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    beneficiary_account = fields.Char(
        string="Beneficiary account", tracking=True, required=True
    )
    account_holder = fields.Char(string="Account holder", tracking=True, required=True)
    receiving_bank_number = fields.Char(
        string="Receiving bank number", tracking=True, required=True
    )
    payer_account = fields.Char(
        string="Payer account", index=True, tracking=True, required=True
    )
    payer_clabe_account = fields.Char(
        string="Payer CLABE account", index=True, tracking=True, required=True, size=18
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    payer_account_holder = fields.Char(
        string="Payer account holder", index=True, tracking=True
    )
    payer_tax_id = fields.Char(string="Payer tax ID", index=True, tracking=True)
    payment_date = fields.Date(string="Payment date", tracking=True, required=True)
    movement_number = fields.Char(
        string="Movement number", tracking=True, required=True
    )
    legend_code = fields.Char(string="Legend code", tracking=True, required=True)
    concept = fields.Char(string="Concept", tracking=True, required=True)
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    actual_cash = fields.Monetary(string="Actual cash")
    numerical_reference = fields.Char(
        string="Numerical reference", tracking=True, copy=False, required=True
    )
    extended_reference = fields.Char(
        string="Extended reference", tracking=True, copy=False
    )
    method_payment = fields.Char(
        string="Method of payment", tracking=True, required=True
    )
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
        string="RSM movement",
        domain="[('state', '=', 'pending_merge')]",
    )
    upload_history_id = fields.Many2one(
        comodel_name="xepelin.movement.upload.history", string="Upload History"
    )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.bnc"
            ) or _("New")
        res = super(MovementBnc, self).create(vals)
        return res

    def write(self, vals):
        result = super(MovementBnc, self).write(vals)
        return result

    def action_merge(self):
        if self.rsm_id and self.state == "pending_merge":
            self.write({"state": "merged"})
            self.rsm_id.write({"state": "merged", "bnc_id": self.id})

    @api.model
    def load(self, fields, data):
        rslt = super(MovementBnc, self).load(fields, data)
        if "import_file" in self.env.context:
            logging.info("==== Import BNC Movements ====")
            logging.info(f"Fields: {fields}")
            logging.info("*" * 50)
            logging.info(f"Data: {data}")
        return rslt

    @api.constrains("payment_date", "numerical_reference", "amount", "movement_number")
    def _check_unique(self):
        for record in self:
            bnc_movement = self.search_count(
                [
                    ("beneficiary_account", "=", record.beneficiary_account),
                    ("payment_date", "=", record.payment_date),
                    ("numerical_reference", "=", record.numerical_reference),
                    ("amount", "=", record.amount),
                    ("movement_number", "=", record.movement_number),
                ]
            )
            if bnc_movement > 1:
                raise ValidationError(
                    _(
                        "An record already exists with the same "
                        "payment_date, numerical reference, amount and movement number."
                    )
                )
