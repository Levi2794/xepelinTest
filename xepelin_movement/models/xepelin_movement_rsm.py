# -*- coding: utf-8 -*-

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MovementRsm(models.Model):
    _name = "xepelin.movement.rsm"
    _description = "RSM Movement"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "date_operation asc"

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    account_number = fields.Char(string="Account", tracking=True, required=True)
    date_operation = fields.Date(string="Date operation", required=True)
    concept = fields.Char(string="Concept", required=True)
    reference = fields.Char(string="Reference", required=True, copy=False)
    extended_reference = fields.Char(
        string="Extended reference", tracking=True, copy=False
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    type = fields.Selection(
        selection=[
            ("charge", "Charge"),
            ("payment", "Payment"),
        ],
        string="Type",
        required=True,
        tracking=True,
    )
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    balance = fields.Monetary(string="Balance", tracking=True)
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
    source = fields.Selection(
        selection=[
            ("rsm", "RSM"),
            ("rsm_spei", "RSM+SPEI"),
            ("rsm_bnc", "RSM+BNC"),
        ],
        default="rsm",
        string="Source",
        readonly=True,
        copy=False,
        tracking=True,
    )
    imported = fields.Boolean(default=False)
    import_date = fields.Date(string="Import date")
    bnc_id = fields.Many2one(comodel_name="xepelin.movement.bnc", string="BNC")
    spei_id = fields.Many2one(comodel_name="xepelin.movement.spei", string="SPEI")
    movement_id = fields.Many2one(
        comodel_name="xepelin.movement.movement", string="Movement", ondelete="cascade"
    )
    upload_history_id = fields.Many2one(
        comodel_name="xepelin.movement.upload.history", string="Upload History"
    )

    @api.constrains("bnc_id", "spei_id")
    def _check_source(self):
        for record in self:
            if record.bnc_id and record.spei_id:
                raise ValidationError(_("The RSM movement can only have one source"))

    @api.constrains("date_operation", "reference", "amount", "type", "balance")
    def _check_unique(self):
        for record in self:
            rsm_movement = self.search_count(
                [
                    ("account_number", "=", record.account_number),
                    ("date_operation", "=", record.date_operation),
                    ("reference", "=", record.reference),
                    ("amount", "=", record.amount),
                    ("type", "=", record.type),
                    ("balance", "=", record.balance),
                ]
            )
            if rsm_movement > 1:
                raise ValidationError(
                    _(
                        f"An record already exists with the same date, reference, amount, type and balance. {self.reference}"
                    )
                )

    @api.onchange("reference")
    def _onchange_reference(self):
        self.reference = self.reference and self.reference.strip()

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.rsm"
            ) or _("New")
        rsm = super(MovementRsm, self).create(vals)
        if not rsm.imported:
            movement_data = {
                "account_number": rsm.account_number,
                "date": rsm.date_operation,
                "concept": rsm.concept,
                "reference": rsm.reference,
                "extended_reference": rsm.extended_reference,
                "amount": rsm.amount,
                "type": rsm.type,
                "balance": rsm.balance,
                "rsm_id": rsm.id,
            }
            self.env["xepelin.movement.movement"].create(movement_data)
        return rsm

    def write(self, vals):
        result = super(MovementRsm, self).write(vals)
        return result
