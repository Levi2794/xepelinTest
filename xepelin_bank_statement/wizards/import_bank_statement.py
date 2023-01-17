# -*- coding: utf-8 -*-

import base64
import io
import logging
import re
import pandas as pd
from datetime import timedelta, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

BCI_COLUMS = [
    "Fecha transacción",
    "Fecha contable (*)",
    "Oficina",
    "Movimiento",
    "N° documento",
    "Cargo (-)",
    "Abono (+)",
    "Glosa detalle",
    "Tipo de compra",
    "Nombre del comercio",
    "Rubro",
    "RUT del comercio",
    "Código de transacción",
    "Servicio",
    "N° Cliente",
    "Empresa",
    "RUT de la empresa",
    "RUT de origen",
    "Nombre de origen",
    "Tipo Cuenta de origen",
    "N° de Cuenta de origen",
    "Banco de origen",
    "Descripción tipo de pago",
    "Correo electrónico",
    "Glosa interna",
    "Código transferencia",
    "RUT destinatario",
    "Nombre destinatario",
    "Tipo Cuenta destinatario",
    "Cuenta destinatario",
    "Banco destinatario",
    "Mail destinatario",
    "Comentario transferencia",
    "Código transferencia.1",
    "Ciudad",
    "Comuna",
    "Tipo de movimiento",
    "Ultimos 4 digitos de tarjeta",
    "N° Operación",
    "Folio",
    "Nombre archivo",
    "Nombre nomina",
    "Fecha de pago",
    "Fecha de carga",
    "Motivo rechazo",
    "RUT empresa facturadora",
    "Razón social empresa facturadora",
    "N° de id",
    "Dirección",
]
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"


class ImportBankStatementWizard(models.TransientModel):
    _name = "import.bank.statement.wizard"
    _description = "Wizard to import bank statements"

    date = fields.Char(default=fields.Date.today)
    account = fields.Char(string="Account")
    name = fields.Char("File Name", readonly=True)
    template = fields.Binary(string="File", attachment=False, required=True)
    type = fields.Selection(
        string="Type", selection=[("bci", "BCI"), ("santander", "Santander")]
    )
    state = fields.Selection(
        [("upload", "upload"), ("uploaded", "uploaded")], default="upload"
    )
    total = fields.Integer(string="Total")
    omitted = fields.Integer(string="Omitted")
    imported = fields.Integer(string="Imported")

    def _process_bci_file(self, template_content):
        try:
            assert ".xlsx" in self.name, "File extension is not .xlsx"
            bank_statement_obj = self.env["xepelin.bank.bci"]
            upload_history_obj = self.env["xepelin.bank.statement.upload.history"]
            df = pd.read_excel(template_content, engine="openpyxl", header=[14])
            df_cols_list = df.columns.tolist()
            assert set(df_cols_list) == set(BCI_COLUMS), "Incorrect column names"
            df["Fecha transacción"] = pd.to_datetime(
                df["Fecha transacción"]
            ).dt.strftime(DATETIME_FORMAT)
            df["Fecha contable (*)"] = pd.to_datetime(
                df["Fecha contable (*)"], dayfirst=True
            ).dt.strftime(DATE_FORMAT)
            df["Fecha de pago"] = pd.to_datetime(df["Fecha de pago"]).dt.strftime(
                DATETIME_FORMAT
            )
            df.fillna("", inplace=True)
            df_dict = df.to_dict("records")
            line_number = 0
            total = len(df_dict)
            omitted = 0
            imported = 0
            repeated_list = []
            currency_env = self.env["res.currency"]
            currency_env = currency_env.search([("name", "=", "CLP")], limit=1)
            try:
                for line in df_dict:
                    line_number += 1
                    transaction_date = line["Fecha transacción"]
                    accounting_date = line["Fecha contable (*)"]
                    office = line["Oficina"]
                    movement = line["Movimiento"]
                    document_number = line["N° documento"]
                    charge = line["Cargo (-)"]
                    payment = line["Abono (+)"]
                    type = "charge" if charge else "payment" if payment else ""
                    amount = charge if charge else payment if payment else 0
                    gloss_detail = line["Glosa detalle"]
                    purchase_type = line["Tipo de compra"]
                    commerce_name = line["Nombre del comercio"]
                    area = line["Rubro"]
                    commerce_rut = line["RUT del comercio"]
                    transaction_code = line["Código de transacción"]
                    service = line["Servicio"]
                    client_number = line["N° Cliente"]
                    company = line["Empresa"]
                    company_rut = line["RUT de la empresa"]
                    origin_rut = line["RUT de origen"]
                    origin_name = line["Nombre de origen"]
                    origin_account_type = line["Tipo Cuenta de origen"]
                    origin_account_number = line["N° de Cuenta de origen"]
                    origin_bank = line["Banco de origen"]
                    payment_type_description = line["Descripción tipo de pago"]
                    email = line["Correo electrónico"]
                    internal_gloss = line["Glosa interna"]
                    transfer_code = line["Código transferencia"]
                    recipient_rut = line["RUT destinatario"]
                    recipient_name = line["Nombre destinatario"]
                    recipient_account_type = line["Tipo Cuenta destinatario"]
                    recipient_account = line["Cuenta destinatario"]
                    recipient_bank = line["Banco destinatario"]
                    recipient_email = line["Mail destinatario"]
                    comment_transfer = line["Comentario transferencia"]
                    city = line["Ciudad"]
                    commune = line["Comuna"]
                    movement_type = line["Tipo de movimiento"]
                    last_four_digits_card = line["Ultimos 4 digitos de tarjeta"]
                    operation_number = line["N° Operación"]
                    folio = line["Folio"]
                    file_name = line["Nombre archivo"]
                    payroll_name = line["Nombre nomina"]
                    payment_date = line["Fecha de pago"] or False
                    upload_date = line["Fecha de carga"] or False
                    rejection_reason = line["Motivo rechazo"]
                    billing_company_rut = line["RUT empresa facturadora"]
                    billing_company_business_name = line[
                        "Razón social empresa facturadora"
                    ]
                    id_number = line["N° de id"]
                    address = line["Dirección"]
                    repeated_domain = [
                        ("transaction_date", "=", transaction_date),
                        ("accounting_date", "=", accounting_date),
                        ("amount", "=", amount),
                        ("type", "=", type),
                        ("operation_number", "=", operation_number),
                    ]
                    bank_statement_repeated = bank_statement_obj.search_count(
                        repeated_domain
                    )
                    if bank_statement_repeated:
                        repeated_list.append(line)
                        omitted += 1
                        continue

                    # Convert str to datetime and add 3 hours
                    transaction_date = datetime.strptime(transaction_date, DATETIME_FORMAT)
                    transaction_date = transaction_date + relativedelta(hours=3)

                    if payment_date:
                        payment_date = datetime.strptime(payment_date, DATETIME_FORMAT)
                        payment_date = payment_date + relativedelta(hours=3)

                    bank_statement_data = {
                        "transaction_date": transaction_date,
                        "accounting_date": accounting_date,
                        "office": office,
                        "movement": movement,
                        "document_number": document_number,
                        "type": type,
                        "amount": amount,
                        "gloss_detail": gloss_detail,
                        "purchase_type": purchase_type,
                        "commerce_name": commerce_name,
                        "area": area,
                        "commerce_rut": commerce_rut,
                        "transaction_code": transaction_code,
                        "service": service,
                        "client_number": client_number,
                        "company": company,
                        "company_rut": company_rut,
                        "origin_rut": origin_rut,
                        "origin_name": origin_name,
                        "origin_account_type": origin_account_type,
                        "origin_account_number": origin_account_number,
                        "origin_bank": origin_bank,
                        "payment_type_description": payment_type_description,
                        "email": email,
                        "internal_gloss": internal_gloss,
                        "transfer_code": transfer_code,
                        "recipient_rut": recipient_rut,
                        "recipient_name": recipient_name,
                        "recipient_account_type": recipient_account_type,
                        "recipient_account": recipient_account,
                        "recipient_bank": recipient_bank,
                        "recipient_email": recipient_email,
                        "comment_transfer": comment_transfer,
                        "city": city,
                        "commune": commune,
                        "movement_type": movement_type,
                        "last_four_digits_card": last_four_digits_card,
                        "operation_number": operation_number,
                        "folio": folio,
                        "file_name": file_name,
                        "payroll_name": payroll_name,
                        "payment_date": payment_date,
                        "upload_date": upload_date,
                        "rejection_reason": rejection_reason,
                        "billing_company_rut": billing_company_rut,
                        "billing_company_business_name": billing_company_business_name,
                        "id_number": id_number,
                        "currency_id": currency_env.id,
                        "address": address,
                    }
                    #print('rrrrrrrrr ', bank_statement_data)
                    bank_statement_obj.create(bank_statement_data)
                    imported += 1
                logging.info(f"Repeateds======>{repeated_list}")
                upload_history_obj.create(
                    {
                        "name": self.name,
                        "type": self.type,
                        "file": self.template,
                        "filename": self.name,
                        "total": total,
                        "imported": imported,
                        "omitted": omitted,
                    }
                )
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                }
            except Exception as e:
                raise UserError(
                    _("Line: %s - An error occurred:\n%s" % (line_number, e))
                )
        except Exception as error:
            self.env.cr.rollback()
            raise ValidationError(_("Error\n%s") % error)

    def _process_santander_file(self, template_content):
        try:
            assert ".xlsx" in self.name, "File extension is not .xlsx"
            bank_statement_obj = self.env["xepelin.bank.santander"]
            upload_history_obj = self.env["xepelin.bank.statement.upload.history"]
            df = pd.read_excel(template_content, engine="openpyxl", header=[11])
            df_cols_list = df.columns.tolist()
            check_list = [
                "MONTO",
                "DESCRIPCIÓN MOVIMIENTO",
                "FECHA",
                "SALDO",
                "N° DOCUMENTO",
                "SUCURSAL",
                "CARGO/ABONO",
            ]
            assert set(df_cols_list) == set(check_list), "Incorrect column names"
            df["FECHA"] = pd.to_datetime(df["FECHA"], format="%d/%m/%Y")
            df.fillna("", inplace=True)
            df_dict = df.to_dict("records")
            line_number = 0
            total = len(df_dict)
            omitted = 0
            imported = 0
            repeated_list = []
            currency_env = self.env["res.currency"]
            currency_env = currency_env.search([("name", "=", "CLP")], limit=1)
            try:
                for line in df_dict:
                    line_number += 1
                    amount = line["MONTO"]
                    movement_description = line["DESCRIPCIÓN MOVIMIENTO"]
                    date = (line["FECHA"] + timedelta(hours=12)).strftime(
                        DATETIME_FORMAT
                    )
                    balance = line["SALDO"]
                    bank_branch = line["SUCURSAL"]
                    if len(movement_description) > 10:
                        rut = movement_description[1:9] + "-" + movement_description[9]
                        rut = (
                            rut
                            if re.match(r"^[0-9]{7,9}-([K|k|0-9]){1}", rut)
                            else None
                        )

                    else:
                        rut = None
                    type = (
                        "charge"
                        if line["CARGO/ABONO"] == "C"
                        else "payment"
                        if line["CARGO/ABONO"] == "A"
                        else ""
                    )
                    repeated_domain = [
                        ("amount", "=", amount),
                        ("movement_description", "=", movement_description),
                        ("date", "=", date),
                        ("balance", "=", balance),
                        ("bank_branch", "=", bank_branch),
                    ]
                    bank_statement_repeated = bank_statement_obj.search_count(
                        repeated_domain
                    )
                    if bank_statement_repeated:
                        repeated_list.append(line)
                        omitted += 1
                        continue
                    bank_statement_data = {
                        "amount": amount,
                        "movement_description": movement_description,
                        "date": date,
                        "balance": balance,
                        "bank_branch": bank_branch,
                        "type": type,
                        "currency_id": currency_env.id,
                        "origin_rut": rut,
                    }
                    bank_statement_obj.create(bank_statement_data)
                    imported += 1
                logging.info(f"Repeated list======>{repeated_list}")
                upload_history_obj.create(
                    {
                        "name": self.name,
                        "type": self.type,
                        "file": self.template,
                        "filename": self.name,
                        "total": total,
                        "imported": imported,
                        "omitted": omitted,
                    }
                )
                return {
                    "type": "ir.actions.client",
                    "tag": "reload",
                }
            except Exception as e:
                raise UserError(
                    _("Line: %s - An error occurred:\n%s" % (line_number, e))
                )
        except Exception as error:
            self.env.cr.rollback()
            raise ValidationError(_("Error\n%s") % error)

    def process_data_action(self):
        try:
            decoded_bytes = base64.b64decode(self.template or b"")
            template_content = io.BytesIO(decoded_bytes)
            return getattr(self, "_process_" + self.type + "_file")(template_content)
        except Exception as error:
            self.env.cr.rollback()
            raise ValidationError(_("An error occurred:\n%s") % error)
