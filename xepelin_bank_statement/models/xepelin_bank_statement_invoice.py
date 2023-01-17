# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class BankStatementInvoice(models.Model):
    _name = "xepelin.bank.statement.invoice"
    _description = "Invoices"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Name", required=True, readonly=True, default=lambda self: _("New")
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    bo_id = fields.Integer(string="BO ID")
    order_id = fields.Many2one(
        "xepelin.bank.statement.order", string="Order", ondelete="cascade"
    )
    status = fields.Char(string="Status")
    verification_status = fields.Char(string="Verification status")
    expiration_date = fields.Date(string="Expiration date")
    debt_date = fields.Char(string="Debt date")
    default_date = fields.Date(string="Default date")
    payment_date = fields.Date(string="Payment date")
    payment_confirmed = fields.Char(string="Payment confirmed")
    base_rate = fields.Float(string="Base rate")
    score = fields.Char(string="Score")
    latest_score_update = fields.Char(string="Latest score update")
    activation_date = fields.Char(string="Activation date")
    created_at = fields.Datetime(string="Created at")
    updated_at = fields.Datetime(string="Updated at")
    # Invoice
    invoice_id = fields.Char(string="Invoice Id")
    identifier = fields.Char(string="Identifier")
    business_id = fields.Integer(string="Business id")
    amount = fields.Monetary(string="Amount")
    folio = fields.Char(string="Folio")
    issue_date = fields.Date(string="Issue date")
    tax_service = fields.Char(string="Tax service")
    invoice_type = fields.Char(string="Invoice type")
    invoice_score = fields.Char(string="Invoice score")
    not_apply_credit_notes = fields.Boolean(
        string="Not apply credit notes", default=False
    )
    invoice_stake_holder_identifier = fields.Char(string="Payer identifier")
    source = fields.Char(string="Source")
    invoice_created_at = fields.Datetime(string="Invoice created at")
    invoice_updated_at = fields.Datetime(string="Invoice updated at")
    state = fields.Selection(
        selection=[("to_reconcile", "To reconcile"), ("reconciled", "Reconciled")],
        string="State",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="to_reconcile",
    )
    # Debt
    payed_interests = fields.Monetary("Payed interests")
    total_capital_debt = fields.Monetary("Total capital debt")
    debt_interest_at_date = fields.Monetary("Debt interest at date")
    total_debt = fields.Monetary("Total debt")
    today_difference_days = fields.Monetary("Today difference days")
    debt_base_rate = fields.Float(string="Debt Base rate")
    segment = fields.Char(string="Segment")
    total_partial_days = fields.Integer(string="Total partial days")
    payer_debt_fd = fields.Monetary(string="Payer debt FD")
    bank_statement_id = fields.Many2one(
        comodel_name="xepelin.bank.bci", string="Bank statement"
    )
    order_number = fields.Char(string="Order number", related="order_id.number")

    def action_reconcile(self):
        self.write({"state": "reconciled"})
        self.bank_statement_id.write({"state": "reconciled"})

    def action_undo_reconcile(self):
        self.write({"state": "to_reconcile"})
        self.bank_statement_id.write({"state": "to_reconcile"})

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.bank.statement.invoice"
            ) or _("New")
        res = super(BankStatementInvoice, self).create(vals)
        return res

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_bank_statement.back_office_cl_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.order_id.number}",
            "target": "new",
        }
