# -*- coding: utf-8 -*-
import datetime
import logging

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATUS_ALLOWED_INVOICES = (
    "ACTIVE",
    "DEFAULT",
    "DELINQUENT",
    "HARD_COLLECTION",
    "HARD_DELINQUENCY",
    "SOFT_DELINQUENCY",
)

STATUS_NOT_INVOICES = (
    "REJECTED",
    "APPROVED",
    "IN_REVIEW",
    "REVIEWED",
    "TO_DEPOSIT",
    "APPEALED",
    "COMPLETE",
    "PAID",
    "",
)


class MovementMovement(models.Model):
    _name = "xepelin.movement.movement"
    _description = "Movements"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "date asc"

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    account_number = fields.Char(string="Account number", tracking=True)
    account_holder = fields.Char(string="Account holder", tracking=True)
    receiving_bank_number = fields.Char(string="Issuing bank", tracking=True)
    payer_bank = fields.Char(string="Payer bank")
    payer_name = fields.Char(string="Payer name")
    payer_account = fields.Char(string="Payer account", index=True, tracking=True)
    payer_clabe_account = fields.Char(
        string="Payer CLABE account", index=True, tracking=True
    )
    payer_tax_id = fields.Char(string="Payer Tax ID", index=True, tracking=True)
    beneficiary_name = fields.Char(string="Beneficiary name")
    beneficiary_bank = fields.Char(string="Beneficiary bank")
    beneficiary_account = fields.Char(string="Beneficiary account")
    date = fields.Datetime(string="Date", tracking=True)
    movement_number = fields.Char(string="Movement number", tracking=True)
    legend_code = fields.Char(string="Legend code", tracking=True)
    concept = fields.Char(string="Concept", tracking=True)
    actual_cash = fields.Monetary(string="Actual cash")
    reference = fields.Char(string="Reference", tracking=True, copy=False)
    numerical_reference = fields.Char(
        string="Numerical reference", tracking=True, copy=False
    )
    extended_reference = fields.Char(
        string="Extended reference", tracking=True, copy=False
    )
    method_payment = fields.Char(string="Method of payment", tracking=True)
    tracking_key = fields.Char(string="Tracking key", required=False)
    payment_status = fields.Char(string="Payment status", required=False)
    return_reason = fields.Char(string="Return reason", required=False)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
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
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    amount = fields.Monetary(string="Amount", tracking=True)
    balance = fields.Monetary(string="Balance", tracking=True)
    type = fields.Selection(
        selection=[
            ("charge", "Charge"),
            ("payment", "Payment"),
        ],
        string="Type",
        required=True,
        tracking=True,
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
    payment_type_ids = fields.Many2many(
        comodel_name="xepelin.movement.payment.type", string="Payment Type"
    )
    rsm_id = fields.Many2one(
        comodel_name="xepelin.movement.rsm", string="RSM", ondelete="cascade"
    )
    order_id = fields.Many2one(
        "xepelin.movement.order", index=True, string="Associated order"
    )
    possible_orders_ids = fields.Many2many(
        "xepelin.movement.order", string="Possible orders"
    )
    order_number = fields.Char(string="Order number", related="order_id.number")

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.movement"
            ) or _("New")
        if vals.get("payer_name"):
            vals["payer_name"] = vals["payer_name"].strip()
        res = super(MovementMovement, self).create(vals)
        return res

    def parser_string_to_datetime(self, dt_string):
        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
        formatted_date = datetime.datetime.strptime(dt_string, date_format)
        return formatted_date

    def get_date_from_datetime_string(self, datetime_str):
        return self.parser_string_to_datetime(datetime_str).date()

    def get_order_discounts(self, discounts):
        return [
            (
                0,
                0,
                {
                    "reason": discount["reason"] or "",
                    "amount": discount["amount"],
                    "external_id": discount["id"],
                },
            )
            for discount in discounts
        ]

    def get_or_create_order(self, order):
        order_env = self.env["xepelin.movement.order"]
        order_rec = order_env.search([("number", "=", order["id"])], limit=1)
        if not order_rec.exists() and order["status"] not in STATUS_NOT_INVOICES:
            order_business = order["Business"]
            order_details = order["OrderDetails"][0]
            order_discounts = order["Discounts"]
            payment_order_detail = order["PaymentOrderDetail"]
            order_data = {
                "number": order["id"],
                "status": order["status"],
                "order_type": order["orderType"],
                "business_id": order_business["id"],
                "business_name": order_business["name"],
                "business_identifier": order_business["identifier"],
                "business_country_id": order_business["countryId"],
                "final_amount": order_details["finalAmount"],
                "transfer": order_details["transfer"],
                "retention": order_details["retencion"],
                "retention_pct": order_details["retentionPct"],
                "advance_payment": order_details["anticipo"],
                "interest": order_details["interes"],
                "base_rate": order_details["tasaBase"],
                "operation_cost": order_details["operationCost"],
                "issued_date": self.parser_string_to_datetime(
                    order_details["issuedDate"]
                ),
                "discount_ids": self.get_order_discounts(order_discounts),
                "has_payer_contribution": payment_order_detail.get(
                    "hasPayerContribution"
                )
                if payment_order_detail != None
                else False,
            }
            order_rec = order_env.sudo().create(order_data)
        return order_rec

    def link_possible_orders(self, order):
        order_rec = self.get_or_create_order(order)
        order_invoices = order.get("OrderInvoices", [])
        active_invoices = [
            invoice
            for invoice in order_invoices
            if invoice["status"] in STATUS_ALLOWED_INVOICES
        ]
        receptors_identifiers = [
            invoice["Invoice"]["invoiceStakeholderIdentifier"]
            for invoice in active_invoices
        ]

        # DIRECT_FINANCING MX and PAYMENTS
        if (
            (
                order_rec.order_type == "DIRECT_FINANCING"
                or order_rec.order_type == "CONFIRMING"
            )
            # Issuer is same as movement
            and order_rec.business_identifier == self.payer_tax_id
            and active_invoices
        ):
            self.write({"possible_orders_ids": [(4, order_rec.id)]})
        # EARLY_PAYMENT --> receptor pays
        elif (
            order_rec.order_type == "EARLY_PAYMENT"
            and self.payer_tax_id in receptors_identifiers
        ):
            self.write({"possible_orders_ids": [(4, order_rec.id)]})
        # Caso intereses payments
        elif (
            order_rec.order_type == "CONFIRMING"
            and order_rec.business_identifier == self.payer_tax_id
            and order_rec.status != "REJECTED"
            and order.get("PaymentOrderDetail")
            and not order["PaymentOrderDetail"]["hasPayerContribution"]
        ):
            self.write({"possible_orders_ids": [(4, order_rec.id)]})
        return order_rec

    def get_invoices_from_bo(self):
        params = self.env["ir.config_parameter"].sudo()
        SG_URL = params.get_param("xepelin_movement.server_global_mx_url")
        SG_TOKEN = params.get_param("xepelin_movement.server_global_mx_token")

        if not SG_URL or not SG_TOKEN:
            raise ValidationError(_("Setup connection to Server Global"))
        URL = f"{SG_URL}/api/backoffice/conciliation/orderinvoice/{self.payer_tax_id}/order/detailbyidentifier"
        headers = {
            "Content-Type": "application/json",
            "Country": self.env.company.country_id.code,
            "Authorization": SG_TOKEN,
        }
        r = requests.get(URL, headers=headers)
        if r.ok:
            data_json = r.json()
            orders = data_json.get("orders", [])
            for order in orders:
                order_rec = self.get_or_create_order(order)
                order_invoices = order.get("OrderInvoices", [])
                self.link_possible_orders(order=order)

                for order_invoice in order_invoices:
                    if order_invoice["status"] not in STATUS_NOT_INVOICES:
                        invoice_match_debt = order_invoice.get("Debt", {})
                        invoice = order_invoice.get("Invoice", {})
                        invoice_data = {
                            "bo_id": order_invoice["id"],
                            "status": order_invoice["status"],
                            "verification_status": order_invoice["verificationStatus"],
                            "expiration_date": self.parser_string_to_datetime(
                                order_invoice["expirationDate"]
                            ),
                            "debt_date": order_invoice["debtDate"],
                            "default_date": order_invoice["defaultDate"],
                            "payment_date": order_invoice["paymentDate"],
                            "payment_confirmed": order_invoice["paymentConfirmed"],
                            "base_rate": order_invoice["baseRate"],
                            "score": order_invoice["score"],
                            "latest_score_update": order_invoice["latestScoreUpdate"],
                            "activation_date": order_invoice["activationDate"],
                            "created_at": self.parser_string_to_datetime(
                                order_invoice["createdAt"]
                            ),
                            "updated_at": self.parser_string_to_datetime(
                                order_invoice["updatedAt"]
                            ),
                            # Invoice
                            "invoice_id": invoice["id"],
                            "identifier": invoice["identifier"],
                            "business_id": invoice["businessId"],
                            "amount": invoice["amount"],
                            "folio": invoice["folio"],
                            "issue_date": self.parser_string_to_datetime(
                                invoice["issueDate"]
                            ),
                            "tax_service": invoice["taxService"],
                            "invoice_type": invoice["invoiceType"],
                            "invoice_score": invoice["score"],
                            "not_apply_credit_notes": invoice["notApplyCreditNotes"],
                            "invoice_stake_holder_identifier": invoice[
                                "invoiceStakeholderIdentifier"
                            ],
                            "source": invoice["source"],
                            "invoice_created_at": self.parser_string_to_datetime(
                                invoice["createdAt"]
                            ),
                            "invoice_updated_at": self.parser_string_to_datetime(
                                invoice["updatedAt"]
                            ),
                            # Debt
                            "payed_interests": invoice_match_debt["payedInterests"],
                            "total_capital_debt": invoice_match_debt[
                                "totalCapitalDebt"
                            ],
                            "debt_interest_at_date": invoice_match_debt[
                                "debtInterestAtDate"
                            ],
                            "total_debt": invoice_match_debt["totalDebt"],
                            "today_difference_days": invoice_match_debt[
                                "todayDifferenceDays"
                            ],
                            "debt_base_rate": invoice_match_debt["baseRate"],
                            "segment": invoice_match_debt["segment"],
                            "total_partial_days": invoice_match_debt["totalPartialPay"],
                            "payer_debt_fd": invoice_match_debt["payerDebtFD"],
                            "movement_id": self.id,
                        }
                        invoice_env = self.env["xepelin.movement.invoice"]
                        invoice_rec = invoice_env.search(
                            [("bo_id", "=", invoice_data["bo_id"])], limit=1
                        )
                        if invoice_rec.exists():
                            order_rec.write(
                                {"invoice_ids": [(1, invoice_rec.id, invoice_data)]}
                            )
                        else:
                            order_rec.write({"invoice_ids": [(0, 0, invoice_data)]})
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "sticky": False,
                    "type": "warning",
                    "message": _(
                        "Error getting information from Server Global  %s" % r.text
                    ),
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }
        return True

    def register_tax_id(self, business_name, tax_id):
        if business_name and tax_id:
            tax_id_history = self.env["xepelin.movement.tax.id.history"]
            tax_id_history_domain = [
                ("business_name", "=like", business_name),
                ("tax_id", "=like", tax_id),
            ]
            tax_id_history_count = tax_id_history.search_count(tax_id_history_domain)
            if tax_id_history_count < 1:
                tax_id_history.create(
                    {"business_name": business_name, "tax_id": tax_id}
                )

    def sanitize_payer_name(self, payer_name):
        payer_name = payer_name.upper()
        mercantil_society_obj = self.env["xepelin.movement.mercantil.society"].search(
            []
        )
        for mercantil in mercantil_society_obj:
            mercantil_name_length = len(mercantil.name)
            # Make sure the last n characters match
            if mercantil.name in payer_name[-mercantil_name_length:]:
                payer_name = payer_name.replace(mercantil.name.upper(), "").strip()
        return payer_name

    def search_rfc(self):
        config_params = self.env["ir.config_parameter"].sudo()
        SG_URL = config_params.get_param("xepelin_movement.server_global_mx_url")
        SG_TOKEN = config_params.get_param("xepelin_movement.server_global_mx_token")
        URL = f"{SG_URL}/api/backoffice/business/"
        country_code = self.env.company.country_id.code
        headers = {
            "Content-Type": "application/json",
            "Country": country_code,
            "Authorization": SG_TOKEN,
        }
        if not SG_URL or not SG_TOKEN:
            raise ValidationError(_("Setup connection to Server Global"))
        tax_id_history = self.env["xepelin.movement.tax.id.history"]
        for record in self:
            if not record.payer_name:
                continue
            tax_id_history_obj = tax_id_history.search(
                [("business_name", "=like", record.payer_name)], limit=1
            )
            if tax_id_history_obj.exists():
                record.payer_tax_id = tax_id_history_obj.tax_id
            else:
                payer_name_sanitize = self.sanitize_payer_name(record.payer_name)
                params = {
                    "searchInput": payer_name_sanitize,
                    "field": "name",
                    "country": country_code,
                }
                r = requests.get(URL, headers=headers, params=params)
                if r.ok:
                    response_json = r.json()
                    r_data = response_json.get("data", [])
                    if r_data:
                        # Assumes no company has the same name than other **
                        tax_id = r_data[0].get("identifier", "")
                        if tax_id:
                            record.payer_tax_id = tax_id
                            self.register_tax_id(record.payer_name, tax_id)
                else:
                    raise ValidationError(
                        _(f"An error ocurred for {record.payer_name}")
                    )

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_movement.back_office_mx_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.order_id.number}",
            "target": "new",
        }
