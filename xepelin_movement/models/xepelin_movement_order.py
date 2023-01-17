# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
import math


class MovementOrder(models.Model):
    _name = "xepelin.movement.order"
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
    order_type = fields.Char("Order type", tracking=True, copy=False, required=True)
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
        comodel_name="xepelin.movement.discount",
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
        comodel_name="xepelin.movement.invoice",
        inverse_name="order_id",
        string="Related invoices",
        required=False,
    )
    # Confirming Params
    has_payer_contribution = fields.Boolean(
        string="Has payer contribution", default=False
    )
    # Odoo params
    movement_ids = fields.One2many(
        comodel_name="xepelin.movement.movement",
        inverse_name="order_id",
        string="Related movements",
        required=False,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    count_invoices = fields.Char(
        compute="_compute_count_invoices", string="Count invoices"
    )
    total_selected_debt = fields.Float(
        compute="_compute_total_lines", string="Total selected debt"
    )
    total_selected_capital = fields.Float(
        compute="_compute_total_lines", string="Total selected capital"
    )
    total_selected_interest = fields.Float(
        compute="_compute_total_lines", string="Total selected interest"
    )
    total_movements = fields.Float(
        compute="_compute_total_lines", string="Total movements"
    )
    total_reconcile = fields.Float(
        compute="_compute_total_reconcile", string="To reconcile total"
    )
    interest_reconcile = fields.Float(
        compute="_compute_total_reconcile", string="To reconcile interest"
    )
    capital_reconcile = fields.Float(
        compute="_compute_total_reconcile", string="To reconcile capital"
    )
    possible_movement_ids = fields.Many2many(
        "xepelin.movement.movement",
        inverse_name="possible_orders_ids",
        string="Possible movements",
        required=False,
    )
    total_payments_interest = fields.Monetary(
        compute="_get_total_payment_interest", string="Total Payment Interest"
    )

    is_same_total_payments_interest = fields.Boolean(
        compute="_compute_is_same", string="Is same payer identifier"
    )
    selected = fields.Boolean(string="Select All Invoices", default=False)

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_movement.back_office_mx_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.number}",
            "target": "new",
        }

    @api.onchange("selected")
    def _onchange_all_selected(self):
        if self.selected == True:
            for inv in self.invoice_ids:
                if inv.status != "COMPLETE":
                    inv.update({"selected": True})
                    self._compute_total_lines()
        else:
            for inv in self.invoice_ids:
                if inv.status != "COMPLETE":
                    inv.update({"selected": False})
                    self._compute_total_lines()

    @api.depends("invoice_ids")
    def _compute_total_lines(self):
        movement_id = self.env.context.get("movement_id")
        for record in self:
            record.total_selected_debt = sum(
                [
                    invoice.total_debt if invoice.selected else 0
                    for invoice in record.invoice_ids
                ]
            )
            record.total_selected_capital = sum(
                [
                    invoice.total_capital_debt if invoice.selected else 0
                    for invoice in record.invoice_ids
                ]
            )
            record.total_selected_interest = sum(
                [
                    invoice.debt_interest_at_date if invoice.selected else 0
                    for invoice in record.invoice_ids
                ]
            )
            record.total_movements = sum(
                [
                    movement.amount if movement._origin.id == movement_id else 0
                    for movement in record.possible_movement_ids
                ]
            )

    @api.depends("invoice_ids")
    def _compute_reconciled(self):
        for record in self:
            if record.invoice_ids.filtered(
                lambda invoice: invoice.state == "to_reconcile"
                and invoice.status == "ACTIVE"
            ):
                record.state = "to_reconcile"
            else:
                record.state = "reconciled"

    @api.depends("invoice_ids")
    def _compute_count_invoices(self):
        for record in self:
            record.count_invoices = len(record.invoice_ids)

    @api.depends(
        "total_selected_debt",
        "total_selected_capital",
        "total_selected_interest",
        "total_movements",
    )
    def _compute_total_reconcile(self):
        for record in self:
            record.total_reconcile = record.total_movements - record.total_selected_debt
            record.interest_reconcile = (
                record.total_movements - record.total_selected_interest
            )
            record.capital_reconcile = (
                record.total_movements - record.total_selected_capital
            )

    def button_reconciled(self):
        movement_id = self.env.context.get("movement_id")
        self.invoice_ids.filtered(lambda invoice: invoice.selected).write(
            {"state": "reconciled", "selected": False}
        )
        self.possible_movement_ids.filtered(
            lambda movment: movment._origin.id == movement_id
        ).write({"state": "reconciled"})

    @api.depends("interest", "operation_cost")
    def _get_total_payment_interest(self):
        for rec in self:
            rec.total_payments_interest = rec.interest + rec.operation_cost

    def _compute_is_same(self):
        movement_id = self.env.context.get("movement_id")
        for record in self:
            if movement_id:
                movement_env = self.env["xepelin.movement.movement"]
                movement_rec = movement_env.search([("id", "=", movement_id)], limit=1)
                record.is_same_total_payments_interest = math.isclose(
                    movement_rec.amount, record.total_payments_interest
                )
            else:
                record.is_same_total_payments_interest = False

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.order"
            ) or _("New")
        res = super(MovementOrder, self).create(vals)
        return res
