# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class BankStatementOrder(models.Model):
    _name = "xepelin.bank.statement.order"
    _description = "Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    number = fields.Char(string="Number", tracking=True, copy=False, required=True)
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    status = fields.Char(string="Status", tracking=True, copy=False)
    business_id = fields.Char(string="Business ID", tracking=True, copy=False)
    business_name = fields.Char(string="Business name", tracking=True, copy=False)
    business_identifier = fields.Char(
        string="Business identifier", tracking=True, copy=False
    )
    business_country_id = fields.Char(
        string="Business country id", tracking=True, copy=False
    )
    final_amount = fields.Monetary(string="Final amount")
    transfer = fields.Monetary(string="Transfer")
    retention = fields.Monetary(string="Retention")
    retention_pct = fields.Monetary(string="Retention PCT")
    advance_payment = fields.Monetary(string="Advance payment")
    interest = fields.Monetary(string="Interest")
    base_rate = fields.Monetary(string="Base rate")
    operation_cost = fields.Monetary(string="Operation cost")
    issued_date = fields.Datetime(string="Issued date")
    discount_ids = fields.One2many(
        comodel_name="xepelin.bank.statement.discount",
        inverse_name="order_id",
        string="Discounts",
    )
    state = fields.Selection(
        selection=[("to_reconcile", "To reconcile"), ("reconciled", "Reconciled")],
        string="State",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="to_reconcile",
    )
    invoice_ids = fields.One2many(
        comodel_name="xepelin.bank.statement.invoice",
        inverse_name="order_id",
        string="Invoices",
        required=False,
    )
    bank_statement_ids = fields.One2many(
        comodel_name="xepelin.bank.bci",
        inverse_name="order_id",
        string="Bank statements",
        required=False,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    count_invoices = fields.Char(
        compute="_compute_count_invoices", string="Count invoices"
    )
    total_invoices = fields.Float(
        compute="_compute_total_lines", string="Total invoices"
    )
    total_movements = fields.Float(
        compute="_compute_total_lines", string="Total movements"
    )
    total_reconcile = fields.Float(
        compute="_compute_total_reconcile", string="To reconcile"
    )

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_bank_statement.back_office_cl_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.number}",
            "target": "new",
        }

    @api.depends("invoice_ids")
    def _compute_total_lines(self):
        for record in self:
            record.total_invoices = sum(
                [invoice.amount for invoice in record.invoice_ids]
            )
            record.total_movements = sum(
                [movement.amount for movement in record.bank_statement_ids]
            )

    @api.depends("invoice_ids")
    def _compute_count_invoices(self):
        for record in self:
            record.count_invoices = len(record.invoice_ids)

    @api.depends("total_invoices", "total_movements")
    def _compute_total_reconcile(self):
        for record in self:
            record.total_reconcile = record.total_invoices - record.total_movements

    def button_reconciled(self):
        self.invoice_ids.filtered(
            lambda invoice: invoice.state == "to_reconcile"
        ).write({"state": "reconciled"})
        self.movement_ids.filtered(
            lambda invoice: invoice.state == "to_reconcile"
        ).write({"state": "reconciled"})
        self.write({"state": "reconciled"})

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.bank.statement.order"
            ) or _("New")
        res = super(BankStatementOrder, self).create(vals)
        return res
