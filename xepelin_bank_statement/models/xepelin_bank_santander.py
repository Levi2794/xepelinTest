# -*- coding: utf-8 -*-

import datetime
import logging
import requests
from pytz import timezone

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATUS_ALLOWED_INVOICES = ("ACTIVE",)


class BankSantander(models.Model):
    _name = "xepelin.bank.santander"
    _description = "Santander Bank statements"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "date asc"

    name = fields.Char(
        string="Id", required=True, readonly=True, default=lambda self: _("New")
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    movement_description = fields.Char(string="Movement Description", tracking=True)
    date = fields.Datetime(string="Movement Date", required=True, tracking=True)
    balance = fields.Monetary(string="Balance", tracking=True)
    bank_branch = fields.Char(string="Company name", tracking=True)
    origin_rut = fields.Char(string="Origin RUT", tracking=True)  # RUT de origen
    type = fields.Selection(
        selection=[
            ("charge", "Charge"),  # Cargo (-)
            ("payment", "Payment"),  # Abono (+)
        ],
        string="Type",
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("to_reconcile", "To reconcile"),
            ("reconciled", "Reconciled"),
        ],
        string="Status",
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default="draft",
    )
    order_id = fields.Many2one(
        comodel_name="xepelin.bank.statement.order", string="Order"
    )
    payment_type_ids = fields.Many2many(
        comodel_name="xepelin.bank.statement.type", string="Payment Type"
    )

    @api.constrains("amount", "movement_description", "date", "balance", "bank_branch")
    def _check_unique(self):
        for record in self:
            bank_statement = self.search_count(
                [
                    ("amount", "=", record.amount),
                    ("movement_description", "=", record.movement_description),
                    ("date", "=", record.date),
                    ("balance", "=", record.balance),
                    ("bank_branch", "=", record.bank_branch),
                ]
            )
            if bank_statement > 1:
                raise ValidationError(
                    _(
                        "There is already a movement with the same "
                        "date, movement_description, amount, balance and bank_branch"
                    )
                )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.bank.santander"
            ) or _("New")
        result = super(BankSantander, self).create(vals)
        return result

    def write(self, vals):
        result = super(BankSantander, self).write(vals)
        return result

    def action_redirect(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xepelin_bank_statement.xepelin_bank_santander_action"
        )
        action["target"] = "main"
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Imported!"),
                "type": "success",
                "sticky": False,
                "message": "Hello world!",
                "next": action,
            },
        }

    def parser_string_to_datetime(self, dt_string):
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        formatted_date = datetime.datetime.strptime(dt_string, date_format)
        return formatted_date

    def get_date_from_datetime_string(self, datetime_str):
        return self.parser_string_to_datetime(datetime_str).date()

    def search_invoices_sg(self):
        logging.info("Searching...")
        return "OK"
