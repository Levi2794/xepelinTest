# -*- coding: utf-8 -*-

import json
import logging

import boto3

from odoo import _, api, fields, models


class MovementInvoice(models.Model):
    _name = "xepelin.movement.invoice"
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
        "xepelin.movement.order", string="Related order", ondelete="cascade"
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

    movement_id = fields.Many2one(
        comodel_name="xepelin.movement.movement",
        string="Movement",
        domain="[('state', '=', 'to_reconcile')]",
    )
    order_number = fields.Char(string="Order number", related="order_id.number")
    # custom params
    selected = fields.Boolean(string=" ", default=False)
    is_same_date = fields.Boolean(compute="_compute_is_same", string="Is same date")
    is_same_amount = fields.Boolean(compute="_compute_is_same", string="Is same amount")
    is_same_payer_identifier = fields.Boolean(
        compute="_compute_is_same", string="Is same payer identifier"
    )

    def action_reconcile(self):
        self.write({"state": "reconciled"})
        self.movement_id.write({"state": "reconciled"})
        params = self.env["ir.config_parameter"].sudo()
        factura_api_dryrun = params.get_param("xepelin_movement.factura_api_dryrun")
        if not factura_api_dryrun:
            factura_api_access_key_id = params.get_param(
                "xepelin_movement.factura_api_access_key_id"
            )
            factura_api_secret_access_key = params.get_param(
                "xepelin_movement.factura_api_secret_access_key"
            )
            factura_api_aws_region = params.get_param(
                "xepelin_movement.factura_api_aws_region"
            )
            factura_api_queue_url = params.get_param(
                "xepelin_movement.factura_api_queue_url"
            )
            if (
                not factura_api_access_key_id
                or not factura_api_secret_access_key
                or not factura_api_aws_region
                or not factura_api_queue_url
            ):
                raise ValueError(_("Incorrect configuration to connect to Factura API"))
            try:
                sqs_client = boto3.client(
                    "sqs",
                    aws_access_key_id=factura_api_access_key_id,
                    aws_secret_access_key=factura_api_secret_access_key,
                    region_name=factura_api_aws_region,
                )
                message = {"invoice_id": self.bo_id}
                response = sqs_client.send_message(
                    QueueUrl=factura_api_queue_url, MessageBody=json.dumps(message)
                )
                logging.info(f"Queue Factura API ack: {response}")
            except Exception as e:
                logging.info(f"Error sending data to Factura API: {str(e)}")

    def _compute_is_same(self):
        movement_id = self.env.context.get("movement_id")
        for record in self:
            if movement_id:
                movement_env = self.env["xepelin.movement.movement"]
                movement_rec = movement_env.search([("id", "=", movement_id)], limit=1)
                record.is_same_date = movement_rec.date.date() == record.expiration_date
                record.is_same_amount = movement_rec.amount == record.amount
                record.is_same_payer_identifier = (
                    record.order_id.order_type == "EARLY_PAYMENT"
                    and movement_rec.payer_tax_id
                    == record.invoice_stake_holder_identifier
                )
            else:
                record.is_same_date = False
                record.is_same_amount = False
                record.is_same_payer_identifier = False

    def action_undo_reconcile(self):
        self.write({"state": "to_reconcile"})
        self.movement_id.write({"state": "to_reconcile"})

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.invoice"
            ) or _("New")
        res = super(MovementInvoice, self).create(vals)
        return res

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_movement.back_office_mx_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.order_id.number}",
            "target": "new",
        }
