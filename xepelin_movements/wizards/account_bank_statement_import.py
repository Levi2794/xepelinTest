# -*- coding: utf-8 -*-

import base64
import io

import pandas as pd

from odoo import _, api, fields, models
from odoo.addons.xepelin_movements.const import MX_BANK_COLUMNS
from odoo.exceptions import UserError, ValidationError


class AccountBankStatementImport(models.TransientModel):
    _inherit = "account.bank.statement.import"

    xepelin_source = fields.Selection(selection=[
        ("spei", "SPEI"),
        ("bnc", "BNC"),
        ("rsm", "RSM"),
        ("cfdi", "Historical CDFI")],
        string="Source Template")
    xepelin_ready = fields.Boolean(string="Ready for Upload", compute="_compute_xepelin_ready")

    @api.depends('xepelin_source','attachment_ids')
    def _compute_xepelin_ready(self):
        for rec in self:
            ready = False
            if all([rec.xepelin_source, rec.attachment_ids]):
                ready = True
            rec.xepelin_ready = ready

    def _check_xlsx(self, filename):
        return filename and filename.lower().strip().endswith('.xlsx')

    def import_file(self):
        if len(self.attachment_ids) > 1:
            raise UserError(_('Only one Spreadsheet (XLSX) file can be selected.'))
        
        if not self._check_xlsx(self.attachment_ids.name):
            raise UserError(_('Can only import Spreadsheet (XLSX) files.'))

        return super(AccountBankStatementImport, self).import_file()

    def _parse_file(self, data_file):
        ctx = dict(self.env.context)
        if ctx.get('journal_id', False):
            journal_id = self.env['account.journal'].browse(ctx['journal_id'])
            if self.xepelin_source:
                try:
                    file_content = io.BytesIO(data_file)
                    return getattr(self, "_process_" + self.xepelin_source + "_file")(file_content, journal_id)
                except Exception as error:
                    self.env.cr.rollback()
                    raise ValidationError(_("An error occurred:\n%s") % error)

            return super(AccountBankStatementImport, self)._parse_file(data_file)

    def _create_bank_statements(self, stmts_vals):
        BankStatement = self.env['account.bank.statement']
        statement_ids, statement_line_ids, notifications = super(AccountBankStatementImport, self)._create_bank_statements(stmts_vals)
        xepelin_source = dict(self._fields['xepelin_source'].selection).get(self.xepelin_source)
        for statement in statement_ids:
            statement_id = BankStatement.browse(statement)
            statement_id.write({
                'xepelin_source': xepelin_source, 
                'xepelin_source_filename': self.attachment_ids.name})

        return statement_ids, statement_line_ids, notifications

    def _process_spei_file(self, template_content, journal_id):
        columns_converters = {
            "Cuenta beneficiario": str,
            "Cuenta ordenante": str,
            "Clave de rastreo": str
        }
        df = pd.read_excel(template_content, engine="openpyxl", skiprows=[
                           0], converters=columns_converters)
        df_cols_list = df.columns.tolist()
        assert all([False for i in df_cols_list if i not in MX_BANK_COLUMNS]
                   ), "Incorrect column names"
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df_dict = df.to_dict("records")
        df_dict = self._check_rsm_values(df_dict)
        vals_bank_statement = []
        currency_lst = [self.env.company.currency_id.name]
        account_lst = list(set([i['Cuenta beneficiario'] for i in df_dict]))

        total_amt = 0.00
        transactions = []
        for line in df_dict:
            vals_line = {
                'date': line['Fecha'],
                'account_number': "%s - %s" % (line['Banco beneficiario'], line['Cuenta beneficiario']),
                'narration': "[%s] %s" % (line['Referencia numerica'], line['Concepto de codigo de leyenda']),
                'payment_ref': '[%s] %s' % (line['Clave de rastreo'], line['Concepto de pago']),
                'ref': line['Referencia'],
                'amount': float(line['Importe']),
                'transaction_type': self._get_transaction_type(float(line['Importe'])),
                'unique_import_id': line['Clave de rastreo'],
                'sequence': len(transactions) + 1,
            }

            bank_account_id = partner_id = False
            partner_bank = self._get_partner_bank(line['Nombre ordenante'], None, line['Cuenta ordenante'],
                                                  line['Banco ordenante'], None, None)
            if partner_bank:
                vals_line['partner_bank_id'] = partner_bank.id
                vals_line['partner_id'] = partner_bank.partner_id.id
            elif line['Nombre ordenante']:
                vals_line['partner_name'] = line['Nombre ordenante']

            total_amt += float(line['Importe'])
            transactions.append(vals_line)

        vals_bank_statement.append({
            'transactions': transactions,
            # 'balance_start': float(line['Saldo']) - total_amt,
            # 'balance_end_real': account.statement.balance,
        })

        if account_lst and len(account_lst) == 1:
            account_lst = account_lst.pop()
            currency_lst = currency_lst.pop()
        else:
            account_lst = None
            currency_lst = None

        return currency_lst, account_lst, vals_bank_statement

    def _process_bnc_file(self, template_content, journal_id):
        columns_converters = {
            "Cuenta beneficiaria": str,
            "Número banco receptor": str,
            "Cuenta CLABE ordenante": str,
            "Cuenta ordenante": str,
            "Número de movimiento": str,
            "Forma de pago": str,
        }
        df = pd.read_excel(template_content, engine="openpyxl",
                           converters=columns_converters)
        df_cols_list = df.columns.tolist()
        assert all([False for i in df_cols_list if i not in MX_BANK_COLUMNS]
                   ), "Incorrect column names"
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")
        df_dict = self._check_rsm_values(df_dict)
        vals_bank_statement = []
        currency_lst = [self.env.company.currency_id.name]
        account_lst = list(set([i['Cuenta beneficiaria'] for i in df_dict]))

        total_amt = 0.00
        transactions = []
        for line in df_dict:
            payment_method = self.env['l10n_mx_edi.payment.method'].search(
                [('code', '=', str(line['Forma de pago']))], limit=1)
            vals_line = {
                'date': line['Fecha de pago'],
                'account_number': "%s - %s" % (line['Titular cuenta'], line['Cuenta beneficiaria']),
                'narration': line['Concepto'],
                'payment_ref': '%s' % (line['Referencia númerica']),
                'ref': line['Referencia númerica'],
                'amount': float(line['Importe']),
                'transaction_type': self._get_transaction_type(float(line['Importe'])),
                'unique_import_id': str(line['Número de movimiento']),
                'sequence': len(transactions) + 1,
                'l10n_mx_edi_payment_method_id': payment_method.id,
                'legend_code': line['Código de leyenda'],
            }

            bank_account_id = partner_id = False
            partner_bank = self._get_partner_bank(line['Titular cuenta ordenante'], line['RFC ordenante'], str(line['Cuenta ordenante']),
                                                  None, line['Número banco receptor'], str(line['Cuenta CLABE ordenante']))
            if partner_bank:
                vals_line['partner_bank_id'] = partner_bank.id
                vals_line['partner_id'] = partner_bank.partner_id.id
            elif line['Titular cuenta ordenante']:
                vals_line['partner_name'] = line['Titular cuenta ordenante']
            
            total_amt += float(line['Importe'])
            transactions.append(vals_line)

        vals_bank_statement.append({
            'transactions': transactions,
            # 'balance_start': float(line['Saldo']) - total_amt,
            # 'balance_end_real': account.statement.balance,
        })

        if account_lst and len(account_lst) == 1:
            currency_lst = currency_lst.pop()
            account_lst = account_lst.pop()
        else:
            account_lst = None
            currency_lst = None

        if journal_id.bank_account_id and \
                account_lst not in journal_id.bank_account_id.acc_number:
            raise ValidationError(
                _("An error occurred: Account number of the extract invalid or not found in the journal."))
        else:
            account_lst = journal_id.bank_account_id.acc_number

        return currency_lst, account_lst, vals_bank_statement

    def get_rsm_amount_type(self, rsm):
        if rsm["Cargo"]:
            m_type = "charge"
            m_amount = -abs(rsm["Cargo"])
        elif rsm["Abono"]:
            m_type = "payment"
            m_amount = rsm["Abono"]
        else:
            raise ValidationError(
                _("Please define an amount for Charge or Payment"))
        return m_type, m_amount

    def _process_rsm_file(self, template_content, journal_id):
        df = pd.read_excel(template_content, engine="openpyxl", skiprows=[0])
        df_cols_list = df.columns.tolist()
        assert all([False for i in df_cols_list if i not in MX_BANK_COLUMNS]
                   ), "Incorrect column names"
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")
        df_dict = self._check_rsm_values(df_dict)
        rsm_repeated_list = []
        total = len(df_dict)
        imported_count = 0
        omitted_count = 0

        vals_bank_statement = []
        account_lst = set()
        currency_lst = set()
        currency_lst.add(self.env.company.currency_id.name)

        total_amt = 0.00
        transactions = []
        for line in df_dict:
            rsm_type, amount = self.get_rsm_amount_type(line)
            vals_line = {
                'date': line['Fecha Operación'],
                'narration': line['Concepto'],
                'payment_ref': '%s' % (line['Referencia Ampliada']),
                'ref': line['Referencia'],
                'amount': amount,
                'transaction_type': rsm_type,
            }
            total_amt += float(line['Saldo'])
            transactions.append(vals_line)

        vals_bank_statement.append({
            'transactions': transactions,
            # 'balance_start': float(line['Saldo']) - total_amt,
            # 'balance_end_real': account.statement.balance,
        })

        if account_lst and len(account_lst) == 1:
            account_lst = account_lst.pop()
            currency_lst = currency_lst.pop()
        else:
            account_lst = None
            currency_lst = None

        return currency_lst, account_lst, vals_bank_statement

    def _process_cfdi_file(self, template_content, journal_id):
        columns_converters = {
            "Cuenta beneficiaria": str,
            "Cuenta ordenante": str,
            "Número de folio de operación": str
        }
        df = pd.read_excel(template_content, engine="openpyxl",
                           converters=columns_converters)  # SPEI
        df_cols_list = df.columns.tolist()
        assert all([False for i in df_cols_list if i not in MX_BANK_COLUMNS]
                   ), "Incorrect column names"
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        df.fillna("", inplace=True)
        df_dict = df.to_dict("records")

        vals_bank_statement = []
        currency_lst = [self.env.company.currency_id.name]
        account_lst = list(set([i['Cuenta beneficiaria'] for i in df_dict]))

        total_amt = 0.00
        transactions = []
        for line in df_dict:
            bank_account_id = partner_id = False
            partner_bank = self._get_partner_bank(
                line['Nombre ordenante'],
                line['RFC ordenante'],
                str(line['Cuenta ordenante']),
                None, None, None,)
            if partner_bank:
                bank_account_id = partner_bank.id
                partner_id = partner_bank.partner_id.id
            payment_method = self.env['l10n_mx_edi.payment.method'].search(
                [('code', '=', str(line['Forma de pago']))], limit=1)
            vals_line = {
                'date': line['Fecha de pago'],
                'account_number': "%s" % (line['Cuenta beneficiaria']),
                'narration': line['Clave producto'],
                'payment_ref': '%s' % (line['Número de folio de operación']),
                'ref': line['Movimiento en cuenta'],
                'amount': float(line['Monto']),
                'transaction_type': self._get_transaction_type(float(line['Monto'])),
                'partner_bank_id': bank_account_id,
                'partner_id': partner_id,
                'unique_import_id': str(line['Número de folio de operación']),
                'sequence': len(transactions) + 1,
                'l10n_mx_edi_payment_method_id': payment_method.id,
            }
            total_amt += float(line['Monto'])
            transactions.append(vals_line)

        vals_bank_statement.append({
            'transactions': transactions,
            # 'balance_start': float(line['Saldo']) - total_amt,
            # 'balance_end_real': account.statement.balance,
        })

        if account_lst and len(account_lst) == 1:
            currency_lst = currency_lst.pop()
            account_lst = account_lst.pop()
        else:
            account_lst = None
            currency_lst = None

        return currency_lst, account_lst, vals_bank_statement

    def _check_rsm_values(self, records):
        source = self.xepelin_source

        if source == "spei":
            return self._clean_rsm_spei(records)
        elif source == "bnc":
            return self._clean_rsm_bnc(records)
        elif source == "rsm":
            return self._clean_rsm_rsm(records)
        else:
            return records

    def _clean_rsm_spei(self, records):
        StatementLine = self.env['account.bank.statement.line']
        lines = []
        for line in records:
            domain = [('date','=',line['Fecha']),('ref','=',line['Referencia']),('amount','=',float(line['Importe']))]
            line_ids = StatementLine.search(domain)
            if not line_ids:
                lines.append(line)

        return lines

    def _clean_rsm_bnc(self, records):
        StatementLine = self.env['account.bank.statement.line']
        lines = []
        for line in records:
            domain = [('date','=',line['Fecha de pago']),('ref','=',line['Referencia númerica']),('amount','=',float(line['Importe']))]
            line_ids = StatementLine.search(domain)
            if not line_ids:
                lines.append(line)

        return lines

    def _clean_rsm_rsm(self, records):
        StatementLine = self.env['account.bank.statement.line']
        lines = []
        for line in records:
            rsm_type, amount = self.get_rsm_amount_type(line)
            domain = [('date','=',line['Fecha Operación']),('ref','=',line['Referencia']),('amount','=',amount)]
            line_ids = StatementLine.search(domain)
            if not line_ids:
                lines.append(line)

        return lines

    def _get_partner_bank(self, payer_name, payer_vat, acc, bank_name, bank_code, cable):
        if not any([payer_name, payer_vat]):
            return False
        
        bank_id = False
        partner_id = False
        partner_bank_id = False
        partner_obj = self.env['res.partner']
        partner_bank_obj = self.env['res.partner.bank']

        try:
            if payer_vat:
                partner_id = partner_obj.search([('vat','=',payer_vat)],limit=1)
                if not partner_id and payer_name:
                    partner_id = partner_obj.search([('name','ilike',payer_name)],limit=1)
                if not partner_id:
                    return False

            elif payer_name:
                partner_id = partner_obj.search([('name','ilike',payer_name)],limit=1)
            
            if partner_id and acc:
                partner_bank_domain = [('partner_id', '=', partner_id.id),('acc_number', '=', acc)]
                partner_bank_id = partner_bank_obj.search(partner_bank_domain, limit=1)
            elif acc:
                partner_bank_domain = [('acc_number', '=', acc)]
                partner_bank_id = partner_bank_obj.search(partner_bank_domain, limit=1)

            if bank_name:
                bank_id = self.env['res.bank'].search(
                    [('name', '=', bank_name)], limit=1)
            elif bank_code:
                bank_id = self.env['res.bank'].search(
                    [('l10n_mx_edi_code', '=', bank_code)], limit=1)

            if not bank_id and bank_name:
                bank_id = bank_id.create({'name': bank_name})

            if not partner_bank_id and all([partner_id.id, acc, bank_id]):
                partner_bank_id = partner_bank_obj.create({
                    "acc_number": acc,
                    "partner_id": partner_id.id,
                    "bank_id": bank_id.id,
                    "l10n_mx_edi_clabe": cable
                })
        except:
            pass

        return partner_bank_id

    def _get_transaction_type(self, amount):
        transaction_type = _("Payment")
        if amount < 0:
            transaction_type = _("Charge")

        return transaction_type
