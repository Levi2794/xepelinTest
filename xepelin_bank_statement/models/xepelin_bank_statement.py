# -*- coding: utf-8 -*-

import datetime
import logging
import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

STATUS_ALLOWED_INVOICES = ("ACTIVE",)


class BankStatement(models.Model):
    _name = "xepelin.bank.statement"
    _description = "Bank statements"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _order = "transaction_date asc"

    name = fields.Char(
        string="#", required=True, readonly=True, default=lambda self: _("New")
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    transaction_date = fields.Datetime(
        string="Transaction Date", required=True, tracking=True
    )  # Fecha transacción
    accounting_date = fields.Date(
        string="Accounting Date", required=True, tracking=True
    )  # Fecha contable (*)
    office = fields.Char(string="Office", required=True, tracking=True)  # Oficina
    movement = fields.Char(
        string="Movement", required=True, tracking=True
    )  # Movimiento
    document_number = fields.Char(
        string="Document number", default="0", tracking=True
    )  # N° documento
    type = fields.Selection(
        selection=[
            ("charge", "Charge"),  # Cargo (-)
            ("payment", "Payment"),  # Abono (+)
        ],
        string="Type",
        required=True,
        tracking=True,
    )
    amount = fields.Monetary(string="Amount", tracking=True, required=True)
    gloss_detail = fields.Char(string="Gloss detail", tracking=True)  # Glosa detalle
    purchase_type = fields.Char(string="Purchase type", tracking=True)  # Tipo de compra
    commerce_name = fields.Char(string="Commerce name")  # Nombre del comercio
    area = fields.Char(string="Area")  # Rubro
    commerce_rut = fields.Char(string="Commerce RUT")  # RUT del comercio
    transaction_code = fields.Char(string="Transaction code")  # Código de transacción
    service = fields.Char(string="Service")  # Servicio
    client_number = fields.Char(string="Client number", tracking=True)  # N° Cliente
    company = fields.Char(string="Company name", tracking=True)  # Empresa
    company_rut = fields.Char(string="Company RUT", tracking=True)  # RUT de la empresa
    origin_rut = fields.Char(string="Origin RUT", tracking=True)  # RUT de origen
    origin_name = fields.Char(string="Origin name", tracking=True)  # Nombre de origen
    origin_account_type = fields.Char(
        string="Origin account type", tracking=True
    )  # Tipo Cuenta de origen
    origin_account_number = fields.Char(
        string="Origin account number", tracking=True
    )  # N° de Cuenta de origen
    origin_bank = fields.Char(string="Origin bank", tracking=True)  # Banco de origen
    payment_type_description = fields.Char(
        string="Payment taype description"
    )  # Descripción tipo de pago
    email = fields.Char(string="Email", tracking=True)  # Correo electrónico
    internal_gloss = fields.Char(
        string="Internal gloss", tracking=True
    )  # Glosa interna
    transfer_code = fields.Char(
        string="Transfer code", tracking=True
    )  # Código transferencia
    recipient_rut = fields.Char(
        string="Recipient RUT", tracking=True
    )  # RUT destinatario
    recipient_name = fields.Char(
        string="Recipient name", tracking=True
    )  # Nombre destinatario
    recipient_account_type = fields.Char(
        string="Recipient account type", tracking=True
    )  # Tipo Cuenta destinatario
    recipient_account = fields.Char(
        string="Recipient account", tracking=True
    )  # Cuenta destinatario
    recipient_bank = fields.Char(
        string="Recipient bank", tracking=True
    )  # Banco destinatario
    recipient_email = fields.Char(
        string="Recipient email", tracking=True
    )  # Mail destinatario
    comment_transfer = fields.Char(
        string="Comment transfer", tracking=True
    )  # Comentario transferencia
    # transfer_code = fields.Char(string='Transfer code')  # Código transferencia / aparece 2 veces con el mismo valor
    city = fields.Char(string="City", tracking=True)  # Ciudad
    commune = fields.Char(string="Commune", tracking=True)  # Comuna
    movement_type = fields.Char(
        string="Movement type", tracking=True
    )  # Tipo de movimiento
    last_four_digits_card = fields.Char(
        string="Last 4 digits card", tracking=True
    )  # Ultimos 4 digitos de tarjeta
    operation_number = fields.Char(
        string="Operation number", tracking=True
    )  # N° Operación
    folio = fields.Char(string="Folio", tracking=True)  # Folio
    file_name = fields.Char(string="File name", tracking=True)  # Nombre archivo
    payroll_name = fields.Char(string="Payroll name", tracking=True)  # Nombre nomina
    payment_date = fields.Datetime(
        string="Payment date", tracking=True
    )  # Fecha de pago
    upload_date = fields.Datetime(string="Upload date")  # Fecha de carga
    rejection_reason = fields.Char(string="Rejection reason")  # Motivo rechazo
    billing_company_rut = fields.Char(
        string="Billing company RUT"
    )  # RUT empresa facturadora
    billing_company_business_name = fields.Char(
        string="Billing company business name"
    )  # Razón social empresa facturadora
    id_number = fields.Char(string="ID number")  # N° de id
    address = fields.Char(string="Address")  # Dirección
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

    @api.constrains("transaction_date", "accounting_date", "amount", "type")
    def _check_unique(self):
        for record in self:
            bank_statement = self.search_count(
                [
                    ("transaction_date", "=", record.transaction_date),
                    ("accounting_date", "=", record.accounting_date),
                    ("amount", "=", record.amount),
                    ("type", "=", record.type),
                    ("operation_number", "=", record.operation_number),
                ]
            )
            if bank_statement > 1:
                raise ValidationError(
                    _(
                        "There is already a movement with the same "
                        "transaction date, accounting date, amount, operation number and type"
                    )
                )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.bank.statement"
            ) or _("New")
        if vals.get("origin_rut"):
            vals["origin_rut"] = vals["origin_rut"].strip()
        if vals.get("origin_name"):
            vals["origin_name"] = vals["origin_name"].strip()
        result = super(BankStatement, self).create(vals)
        return result

    def write(self, vals):
        result = super(BankStatement, self).write(vals)
        return result

    def action_redirect(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "xepelin_bank_statement.xepelin_bank_statement_action"
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
        order_env = self.env["xepelin.bank.statement.order"]
        order_rec = order_env.search([("number", "=", order["id"])], limit=1)
        if not order_rec.exists():
            order_business = order["Business"]
            order_details = order["OrderDetails"][0]
            order_discounts = order["Discounts"]
            order_data = {
                "number": order["id"],
                "status": order["status"],
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
            }
            order_rec = order_env.sudo().create(order_data)
        return order_rec

    def search_invoices_sg(self):
        # date = self.transaction_date.date()
        date = self.accounting_date
        amount = self.amount
        params = self.env["ir.config_parameter"].sudo()
        SG_URL = params.get_param("xepelin_bank_statement.server_global_cl_url")
        SG_TOKEN = params.get_param("xepelin_bank_statement.server_global_cl_token")

        if not SG_URL or not SG_TOKEN:
            raise ValidationError(_("Setup connection to Server Global"))
        URL = f"{SG_URL}/api/backoffice/conciliation/orderinvoice/{self.origin_rut}/order/detailbyidentifier"
        headers = {
            "Content-Type": "application/json",
            "Country": self.env.company.country_id.code,
            "Authorization": SG_TOKEN,
        }
        r = requests.get(URL, headers=headers)
        if r.ok:
            data_json = r.json()
            orders = data_json.get("orders", [])
            match = False
            for order in orders:
                order_business = order["Business"]
                invoices = order.get("OrderInvoices", [])
                active_invoices = [
                    invoice
                    for invoice in invoices
                    if invoice["status"] in STATUS_ALLOWED_INVOICES
                ]
                today_invoices = [
                    invoice
                    for invoice in active_invoices
                    if self.get_date_from_datetime_string(invoice["expirationDate"])
                    == date
                ]
                amount_invoices = [
                    invoice
                    for invoice in today_invoices
                    if invoice["Invoice"]["amount"] == amount
                ]
                rut_invoices = [
                    invoice
                    for invoice in amount_invoices
                    if invoice["Invoice"]["invoiceStakeholderIdentifier"]
                    == self.origin_rut
                ]
                if rut_invoices:
                    order_rec = self.get_or_create_order(order)
                    invoice_match = rut_invoices[0]
                    invoice_match_debt = invoice_match.get("Debt", {})
                    invoice_match_invoice = invoice_match.get("Invoice", {})
                    invoice_data = {
                        "bo_id": invoice_match["id"],
                        "status": invoice_match["status"],
                        "verification_status": invoice_match["verificationStatus"],
                        "expiration_date": self.parser_string_to_datetime(
                            invoice_match["expirationDate"]
                        ),
                        "debt_date": invoice_match["debtDate"],
                        "default_date": invoice_match["defaultDate"],
                        "payment_date": invoice_match["paymentDate"],
                        "payment_confirmed": invoice_match["paymentConfirmed"],
                        "base_rate": invoice_match["baseRate"],
                        "score": invoice_match["score"],
                        "latest_score_update": invoice_match["latestScoreUpdate"],
                        "activation_date": invoice_match["activationDate"],
                        "created_at": self.parser_string_to_datetime(
                            invoice_match["createdAt"]
                        ),
                        "updated_at": self.parser_string_to_datetime(
                            invoice_match["updatedAt"]
                        ),
                        # Invoice
                        "invoice_id": invoice_match_invoice["id"],
                        "identifier": invoice_match_invoice["identifier"],
                        "business_id": invoice_match_invoice["businessId"],
                        "amount": invoice_match_invoice["amount"],
                        "folio": invoice_match_invoice["folio"],
                        "issue_date": self.parser_string_to_datetime(
                            invoice_match_invoice["issueDate"]
                        ),
                        "tax_service": invoice_match_invoice["taxService"],
                        "invoice_type": invoice_match_invoice["invoiceType"],
                        "invoice_score": invoice_match_invoice["score"],
                        "not_apply_credit_notes": invoice_match_invoice[
                            "notApplyCreditNotes"
                        ],
                        "invoice_stake_holder_identifier": invoice_match_invoice[
                            "invoiceStakeholderIdentifier"
                        ],
                        "source": invoice_match_invoice["source"],
                        "invoice_created_at": self.parser_string_to_datetime(
                            invoice_match_invoice["createdAt"]
                        ),
                        "invoice_updated_at": self.parser_string_to_datetime(
                            invoice_match_invoice["updatedAt"]
                        ),
                        # Debt
                        "payed_interests": invoice_match_debt["payedInterests"],
                        "total_capital_debt": invoice_match_debt["totalCapitalDebt"],
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
                        "bank_statement_id": self.id,
                    }
                    order_rec.write({"invoice_ids": [(0, 0, invoice_data)]})
                    self.write({"order_id": order_rec, "state": "to_reconcile"})
                    match = True
                    break
            if match:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "sticky": False,
                        "type": "success",
                        "message": _(
                            "An invoice was found that matches the data for the movement %s"
                            % self.name
                        ),
                        "next": {"type": "ir.actions.act_window_close"},
                    },
                }
            else:
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "type": "info",
                        "sticky": False,
                        "message": _(
                            "Invoices not found for the movement %s" % self.name
                        ),
                        "next": {"type": "ir.actions.act_window_close"},
                    },
                }
        else:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "type": "warning",
                    "sticky": False,
                    "message": _("Serve global error: %s" % r.content),
                    "next": {"type": "ir.actions.act_window_close"},
                },
            }

    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_bank_statement.back_office_cl_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.order_id.number}",
            "target": "new",
        }
