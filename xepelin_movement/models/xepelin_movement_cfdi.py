# -*- coding: utf-8 -*-
import logging
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MovementCfdi(models.Model):
    _name = "xepelin.movement.cfdi"
    _description = "Historical SPEI"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _check_company_auto = True
    _sql_constraints = [
        ("cfdi_rsm_unique", "unique (rsm_id)", "The RSM can only be linked once"),
    ]
    _order = "date asc"

    name = fields.Char(
        string="Folio", required=True, readonly=True, default=lambda self: _("New")
    )
    key_product = fields.Char(string="Key Product", required=True)  # Clave producto
    date = fields.Datetime(string="Date", required=False)  # Fecha de pago
    payment_method = fields.Char(
        string="Payment Method", required=True
    )  # Forma de pago
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id.id,
    )
    exchange_rate = fields.Monetary(
        string="Exchange Rate", required=False
    )  # Tipo de cambio
    amount = fields.Monetary(string="Amount", required=False)  # Monto
    operation_folio_number = fields.Char(
        string="Folio Number", required=False
    )  # Número de folio de operación
    account_movement = fields.Char(
        string="Account Movement", required=False
    )  # Movimiento en cuenta
    payer_bank_tax_id = fields.Char(
        string="Payer Bank Tax ID", required=False
    )  # RFC Banco ordenante
    payer_bank = fields.Char(
        string="Payer Bank", required=False
    )  # Nombre banco ordenante
    payer_tax_id = fields.Char(string="Payer Tax ID", required=False)  # RFC ordenante
    payer_name = fields.Char(string="Payer name", required=False)  # Nombre ordenante
    payer_clabe_account = fields.Char(
        string="Payer CLABE Account", required=False
    )  # Cuenta ordenante
    beneficiary_bank_tax_id = fields.Char(
        string="Beneficiary Bank Tax ID", required=False
    )  # RFC Banco beneficiario
    beneficiary_clabe_account = fields.Char(
        string="Beneficiary CLABE Account", required=True
    )  # Cuenta beneficiaria
    payment_chain_type = fields.Char(
        string="Payment Chain Type", required=False
    )  # Tipo de cadena de pago
    payment_certificate = fields.Char(
        string="Payment Certificate", required=False
    )  # Certificado del pago
    original_chain = fields.Char(
        string="Original Chain", required=False
    )  # Cadena original
    payment_stamp = fields.Char(string="Payment Stamp", required=False)  # Sello de pago
    operation_folio = fields.Char(
        string="Operation Folio", required=False
    )  # Folio de operación
    beneficiary_account = fields.Char(
        string="Beneficiary Account", required=False
    )  # Cuenta
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
    rsm_id = fields.Many2one(
        comodel_name="xepelin.movement.rsm",
        string="RSM Movement",
        domain="[('state', '=', 'pending_merge')]",
    )
    upload_history_id = fields.Many2one(
        comodel_name="xepelin.movement.upload.history", string="Upload History"
    )

    @api.constrains(
        "date", "amount", "original_chain", "payment_stamp", "operation_folio"
    )
    def _check_unique(self):
        for record in self:
            cfdi_movement = self.search_count(
                [
                    ("date", "=", record.date),
                    ("amount", "=", record.amount),
                    ("original_chain", "=", record.original_chain),
                    ("payment_stamp", "=", record.payment_stamp),
                    ("operation_folio", "=", record.operation_folio),
                ]
            )
            if cfdi_movement > 1:
                raise ValidationError(
                    _(
                        "An record already exists with the same "
                        "date, amount, original chain, payment stamp and operation folio."
                    )
                )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "xepelin.movement.cfdi"
            ) or _("New")
        res = super(MovementCfdi, self).create(vals)
        return res

    def write(self, values):
        result = super(MovementCfdi, self).write(values)
        return result

    def action_merge(self):
        if self.rsm_id and self.state == "pending_merge":
            self.write({"state": "merged"})
            self.rsm_id.write({"state": "merged", "cfdi_id": self.id})
