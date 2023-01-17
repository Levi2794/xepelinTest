# -*- coding: utf-8 -*-

import base64
import io
import logging

import pandas as pd

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ImportSourceMovementWizard(models.TransientModel):
    _name = "import.source.movement.wizard"
    _description = "Wizard to import source movements"

    date = fields.Char(default=fields.Date.today)
    account = fields.Char(string="Account")
    name = fields.Char("File Name", readonly=True)
    template = fields.Binary(string="File", attachment=False, required=True)
    type = fields.Selection(
        string="Type",
        selection=[("rsm", "RSM"), ("spei", "SPEI"), ("cfdi", "CFDI"), ("bnc", "BNC")],
    )
    state = fields.Selection(
        [("upload", "upload"), ("uploaded", "uploaded")], default="upload"
    )
    omitted = fields.Integer(string="Omitted")
    imported = fields.Integer(string="Imported")

    def get_tax_id(self, payer_name):
        tax_id = ""
        tax_id_history = self.env["xepelin.movement.tax.id.history"]
        tax_id_history_rec = tax_id_history.search(
            [("business_name", "=like", payer_name)], limit=1
        )
        if tax_id_history_rec.exists():
            tax_id = tax_id_history_rec.tax_id
        return tax_id

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

    def get_rsm_amount_type(self, rsm):
        if rsm["Cargo"]:
            m_type = "charge"
            m_amount = -abs(rsm["Cargo"])
        elif rsm["Abono"]:
            m_type = "payment"
            m_amount = rsm["Abono"]
        else:
            raise ValidationError(_("Please define an amount for Charge or Payment"))
        return m_type, m_amount

    def _process_rsm_file(self, template_content):
        date = self.date
        rsm_obj = self.env["xepelin.movement.rsm"]
        movement_obj = self.env["xepelin.movement.movement"]
        upload_history_obj = self.env["xepelin.movement.upload.history"]
        df = pd.read_excel(template_content, engine="openpyxl", header=[0, 1])
        account_number = df.columns[1][0]
        df.columns = df.columns.droplevel(0)
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")
        rsm_repeated_list = []
        total = len(df_dict)
        imported_count = 0
        omitted_count = 0
        for rsm in df_dict:
            rsm_type, amount = self.get_rsm_amount_type(rsm)
            account_number = str(account_number).strip()
            date_operation = rsm["Fecha Operación"]
            concept = str(rsm["Concepto"]).strip()
            reference = str(rsm["Referencia"]).strip()
            extended_reference = str(rsm["Referencia Ampliada"]).strip()
            balance = rsm["Saldo"]
            rsm_repeated = rsm_obj.search_count(
                [
                    ("account_number", "=", account_number),
                    ("date_operation", "=", date_operation),
                    ("reference", "=", reference),
                    ("amount", "=", amount),
                    ("type", "=", rsm_type),
                    ("balance", "=", balance),
                ]
            )
            if rsm_repeated:
                logging.info(f"RSM repeated: {rsm}")
                rsm_repeated_list.append(rsm)
                omitted_count += 1
                continue
            rsm_data = {
                "account_number": account_number,
                "date_operation": date_operation,
                "concept": concept,
                "reference": reference,
                "extended_reference": extended_reference,
                "amount": amount,
                "type": rsm_type,
                "balance": balance,
                "imported": True,
                "import_date": date,
            }
            rsm_id = rsm_obj.create(rsm_data)
            movement_data = {
                "account_number": account_number,
                "date": rsm_data["date_operation"],
                "concept": rsm_data["concept"],
                "reference": str(rsm_data["reference"]).strip(),
                "extended_reference": str(rsm_data["extended_reference"]).strip(),
                "amount": rsm_data["amount"],
                "type": rsm_data["type"],
                "balance": rsm_data["balance"],
                "rsm_id": rsm_id.id,
            }
            movement_id = movement_obj.create(movement_data)
            rsm_id.write({"movement_id": movement_id.id})
            imported_count += 1

        logging.info(f"Imported==========>{imported_count}")
        logging.info(f"Omitted==========>{omitted_count}")
        upload_history_obj.create(
            {
                "name": self.name,
                "type": self.type,
                "file": self.template,
                "filename": self.name,
                "total": total,
                "imported": imported_count,
                "omitted": omitted_count,
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def _process_spei_file(self, template_content):
        rsm_obj = self.env["xepelin.movement.rsm"]
        spei_obj = self.env["xepelin.movement.spei"]
        upload_history_obj = self.env["xepelin.movement.upload.history"]
        import_date = self.date
        df = pd.read_excel(template_content, engine="openpyxl", header=[0, 1])
        account_number = str(df.columns[1][0]).strip()
        df.columns = df.columns.droplevel(0)
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df_dict = df.to_dict("records")
        spei_repeated_list = []
        total = len(df_dict)
        imported_count = 0
        omitted_count = 0
        for spei in df_dict:
            date = spei["Fecha"] or False
            numerical_reference = str(spei["Referencia numerica"]).strip()
            legend_code_concept = spei["Concepto de codigo de leyenda"]
            reference = spei["Referencia"]
            concept = spei["Concepto de pago"]
            amount = spei["Importe"]
            balance = spei["Saldo"]
            payer_bank = spei["Banco ordenante"]
            payer_name = spei["Nombre ordenante"]
            payer_account = spei["Cuenta ordenante"]
            beneficiary_name = spei["Banco beneficiario"]
            beneficiary_bank = spei["Nombre beneficiario"]
            beneficiary_account = spei["Cuenta beneficiario"]
            tracking_key = str(spei["Clave de rastreo"]).strip()
            payment_status = spei["Estado del pago"]
            return_reason = spei["Motivo de devolucion"]
            spei_repeated = spei_obj.search_count(
                [
                    ("account_number", "=", account_number),
                    ("date", "=", date),
                    ("numerical_reference", "=", numerical_reference),
                    ("amount", "=", amount),
                    ("tracking_key", "=", tracking_key),
                    ("balance", "=", balance),
                ]
            )
            if spei_repeated:
                logging.info(f"Skip SPEI repeated: {spei}")
                spei_repeated_list.append(spei)
                omitted_count += 1
                continue
            spei_data = {
                "account_number": account_number,
                "date": date,
                "numerical_reference": numerical_reference,
                "legend_code_concept": legend_code_concept,
                "reference": reference,
                "concept": concept,
                "amount": amount,
                "balance": balance,
                "payer_bank": payer_bank,
                "payer_name": payer_name,
                "payer_account": payer_account,
                "beneficiary_name": beneficiary_name,
                "beneficiary_bank": beneficiary_bank,
                "beneficiary_account": beneficiary_account,
                "tracking_key": tracking_key,
                "payment_status": payment_status,
                "return_reason": return_reason,
                "imported": True,
                "import_date": import_date,
            }
            spei_id = spei_obj.create(spei_data)
            rsm_domain = [
                ("account_number", "=", account_number),
                ("reference", "=", reference),
                ("date_operation", "=", date),
                ("amount", "=", amount),
                ("state", "=", "pending_merge"),
                ("spei_id", "=", False),
                ("type", "=", "payment"),
            ]
            rsm_id = rsm_obj.search(rsm_domain, limit=1)
            if rsm_id.exists():
                spei_id.write({"rsm_id": rsm_id.id, "state": "merged"})
                rsm_id.write(
                    {"spei_id": spei_id, "state": "merged", "source": "rsm_spei"}
                )
                movement_id = rsm_id.movement_id
                movement_data = {
                    "account_number": account_number,  # RSM
                    # 'account_holder': '',
                    "receiving_bank_number": payer_bank,
                    "payer_bank": payer_bank,
                    "payer_name": payer_name,
                    "payer_account": payer_account,
                    # 'payer_clabe_account': '',
                    "payer_tax_id": self.get_tax_id(payer_name),
                    "beneficiary_name": beneficiary_name,
                    "beneficiary_bank": beneficiary_bank,
                    "beneficiary_account": beneficiary_account,
                    "date": date,  # RSM
                    # 'movement_number': '',
                    "legend_code": legend_code_concept,
                    "concept": f"{movement_id.concept}/{concept}",  # RSM
                    # 'actual_cash': '',
                    "reference": reference,  # RSM
                    "numerical_reference": numerical_reference,
                    # 'extended_reference': '',  # RSM
                    # 'method_payment': '',
                    "tracking_key": tracking_key,
                    "payment_status": payment_status,
                    "return_reason": return_reason,
                    # 'amount': spei_data['amount'],  # RSM
                    # 'balance': spei_data['balance'],  # RSM
                    "source": "rsm_spei",
                }
                movement_id.write(movement_data)
            imported_count += 1
        logging.info(f"SPEI Imported==========>{imported_count}")
        logging.info(f"SPEI Omitted==========>{omitted_count}")
        upload_history_obj.create(
            {
                "name": self.name,
                "type": self.type,
                "file": self.template,
                "filename": self.name,
                "total": total,
                "imported": imported_count,
                "omitted": omitted_count,
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def _process_cfdi_file(self, template_content):
        rsm_obj = self.env["xepelin.movement.rsm"]
        cfdi_obj = self.env["xepelin.movement.cfdi"]
        upload_history_obj = self.env["xepelin.movement.upload.history"]
        df = pd.read_excel(template_content, engine="openpyxl")  # SPEI
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")
        cfdi_repeated_list = []
        total = len(df_dict)
        imported_count = 0
        omitted_count = 0
        for cfdi in df_dict:
            key_product = cfdi["Clave producto"]
            date = cfdi["Fecha de pago"]
            payment_method = cfdi["Forma de pago"]
            exchange_rate = cfdi["Tipo de cambio"]
            amount = cfdi["Monto"]
            operation_folio_number = cfdi["Número de folio de operación"]
            account_movement = cfdi["Movimiento en cuenta"]
            payer_bank_tax_id = cfdi["RFC Banco ordenante"]
            payer_bank = cfdi["Nombre banco ordenante"]
            payer_tax_id = cfdi["RFC ordenante"]
            payer_name = cfdi["Nombre ordenante"]
            payer_clabe_account = cfdi["Cuenta ordenante"]
            beneficiary_bank_tax_id = cfdi["RFC Banco beneficiario"]
            beneficiary_clabe_account = cfdi["Cuenta beneficiaria"]
            payment_chain_type = cfdi["Tipo de cadena de pago"]
            payment_certificate = cfdi["Certificado del pago"]
            original_chain = cfdi["Cadena original"]
            payment_stamp = cfdi["Sello de pago"]
            operation_folio = cfdi["Folio de operación"]
            beneficiary_account = cfdi["Cuenta"]
            cfdi_repeated = cfdi_obj.search_count(
                [
                    ("date", "=", date),
                    ("amount", "=", amount),
                    ("original_chain", "=", original_chain),
                    ("payment_stamp", "=", payment_stamp),
                    ("operation_folio", "=", operation_folio),
                ]
            )
            if cfdi_repeated:
                logging.info(f"Skip CFDI repeated: {cfdi}")
                cfdi_repeated_list.append(cfdi)
                omitted_count += 1
                continue
            cfdi_data = {
                "key_product": key_product,
                "date": date,
                "original_chain": original_chain,
                "payment_method": payment_method,
                "exchange_rate": exchange_rate,
                "amount": amount,
                "operation_folio_number": operation_folio_number,
                "operation_folio": operation_folio,
                "account_movement": account_movement,
                "payer_bank_tax_id": payer_bank_tax_id,
                "payer_bank": payer_bank,
                "payer_tax_id": payer_tax_id,
                "payer_name": payer_name,
                "payer_clabe_account": payer_clabe_account,
                "beneficiary_bank_tax_id": beneficiary_bank_tax_id,
                "beneficiary_clabe_account": beneficiary_clabe_account,
                "payment_chain_type": payment_chain_type,
                "payment_certificate": payment_certificate,
                "beneficiary_account": beneficiary_account,
                "payment_stamp": payment_stamp,
            }

            # cfdi_id = cfdi_obj.create(cfdi_data)
            logging.info(beneficiary_account)
            cfdi_obj.create(cfdi_data)
            imported_count += 1
        upload_history_obj.create(
            {
                "name": self.name,
                "type": self.type,
                "file": self.template,
                "filename": self.name,
                "total": total,
                "imported": imported_count,
                "omitted": omitted_count,
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def _process_bnc_file(self, template_content):
        rsm_obj = self.env["xepelin.movement.rsm"]
        bnc_obj = self.env["xepelin.movement.bnc"]
        upload_history_obj = self.env["xepelin.movement.upload.history"]
        import_date = self.date
        columns_converters = {
            "Cuenta beneficiaria": str,
            "Número banco receptor": str,
            "Cuenta CLABE ordenante": str,
            "Cuenta ordenante": str,
            "Número de movimiento": str,
            "Forma de pago": str,
        }
        df = pd.read_excel(
            template_content, engine="openpyxl", converters=columns_converters
        )
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")
        bnc_repeated_list = []
        total = len(df_dict)
        imported_count = 0
        omitted_count = 0
        for bnc in df_dict:
            beneficiary_account = bnc["Cuenta beneficiaria"].strip()
            account_holder = bnc["Titular cuenta"].strip()
            receiving_bank_number = bnc["Número banco receptor"].strip()
            payer_account = bnc["Cuenta ordenante"].strip()
            payer_clabe_account = bnc["Cuenta CLABE ordenante"].strip()
            payer_account_holder = bnc["Titular cuenta ordenante"].strip()
            payer_tax_id = bnc["RFC ordenante"].strip() or self.get_tax_id(
                payer_account_holder
            )
            payment_date = bnc["Fecha de pago"]
            movement_number = bnc["Número de movimiento"].strip()
            legend_code = bnc["Código de leyenda"].strip()
            concept = bnc["Concepto"].strip()
            amount = bnc["Importe"]
            actual_cash = bnc["Efectivo real"]
            numerical_reference = bnc["Referencia númerica"].strip()
            extended_reference = bnc["Referencia ampliada"].strip()
            method_payment = bnc["Forma de pago"].strip()
            self.register_tax_id(payer_account_holder, payer_tax_id)
            bnc_repeated = bnc_obj.search_count(
                [
                    ("beneficiary_account", "=", beneficiary_account),
                    ("payment_date", "=", payment_date),
                    ("numerical_reference", "=", numerical_reference),
                    ("amount", "=", amount),
                    ("movement_number", "=", movement_number),
                ]
            )
            if bnc_repeated:
                logging.info(f"Skip BNC repeated: {bnc}")
                bnc_repeated_list.append(bnc)
                omitted_count += 1
                continue
            bnc_data = {
                "beneficiary_account": beneficiary_account,
                "account_holder": account_holder,
                "receiving_bank_number": receiving_bank_number,
                "payer_account": payer_account,
                "payer_clabe_account": payer_clabe_account,
                "payer_account_holder": payer_account_holder,
                "payer_tax_id": payer_tax_id,
                "payment_date": payment_date,
                "movement_number": movement_number,
                "legend_code": legend_code,
                "concept": concept,
                "amount": amount,
                "actual_cash": actual_cash,
                "numerical_reference": numerical_reference,
                "extended_reference": extended_reference,
                "method_payment": method_payment,
                "imported": True,
                "import_date": import_date,
            }
            bnc_id = bnc_obj.create(bnc_data)
            rsm_domain = [
                ("account_number", "=", beneficiary_account),
                ("reference", "=", numerical_reference),
                ("date_operation", "=", payment_date),
                ("amount", "=", amount),
                ("state", "=", "pending_merge"),
                ("bnc_id", "=", False),
                ("type", "=", "payment"),
            ]
            rsm_id = rsm_obj.search(rsm_domain, limit=1)
            if rsm_id.exists():
                bnc_id.write({"rsm_id": rsm_id.id, "state": "merged"})
                rsm_id.write({"bnc_id": bnc_id, "state": "merged", "source": "rsm_bnc"})
                movement_id = rsm_id.movement_id
                movement_data = {
                    "account_number": beneficiary_account,  # RSM
                    "account_holder": account_holder,
                    "receiving_bank_number": receiving_bank_number,
                    # 'payer_bank': '',
                    "payer_name": payer_account_holder,
                    "payer_account": payer_account,
                    "payer_clabe_account": payer_clabe_account,
                    "payer_tax_id": payer_tax_id,
                    # 'beneficiary_name': '',
                    # 'beneficiary_bank': '',
                    # 'beneficiary_account': '',
                    "date": payment_date,  # RSM
                    "movement_number": movement_number,
                    "legend_code": legend_code,
                    "concept": concept,  # RSM
                    "actual_cash": actual_cash,
                    # 'reference': '',  # RSM
                    "numerical_reference": numerical_reference,
                    "extended_reference": extended_reference,  # RSM
                    "method_payment": method_payment,
                    # 'tracking_key': '',
                    # 'payment_status': '',
                    # 'return_reason': '',
                    # 'amount': amount,  # RSM
                    # 'balance': '',  # RSM
                    "source": "rsm_bnc",
                }
                movement_id.write(movement_data)
            imported_count += 1
        logging.info(f"Imported==========>{imported_count}")
        logging.info(f"Omitted==========>{omitted_count}")
        upload_history_obj.create(
            {
                "name": self.name,
                "type": self.type,
                "file": self.template,
                "filename": self.name,
                "total": total,
                "imported": imported_count,
                "omitted": omitted_count,
            }
        )
        return {
            "type": "ir.actions.client",
            "tag": "reload",
        }

    def process_data_action(self):
        try:
            decoded_bytes = base64.b64decode(self.template or b"")
            template_content = io.BytesIO(decoded_bytes)
            return getattr(self, "_process_" + self.type + "_file")(template_content)
        except Exception as error:
            self.env.cr.rollback()
            raise ValidationError(_("An error occurred:\n%s") % error)
