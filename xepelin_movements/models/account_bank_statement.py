# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    xepelin_source = fields.Char(string="File Source")
    xepelin_source_filename = fields.Char(string="File name")
    xepelin_enable_orderinvoice_search = fields.Boolean(string="Enable OrderInvoice search", compute="_compute_enable_orderinvoice_search")

    @api.depends('line_ids')
    def _compute_enable_orderinvoice_search(self):
        for rec in self:
            enable = False
            if rec.line_ids:
                rfc_exist = rec.line_ids.mapped('partner_id.vat')
                if rfc_exist:
                    enable = True

            rec.xepelin_enable_orderinvoice_search = enable

    def xepelin_orderinvoice_search(self):
        self.ensure_one()
        partner_ids = self.line_ids.filtered(lambda l: l.partner_id.vat).mapped('partner_id')
        return {
            'type': 'ir.actions.act_window',
            'name': _("Search Order-Invoices"),
            'res_model': 'search.orderinvoice.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_ids': [(6,0,partner_ids.ids)]}
        }


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    legend_code = fields.Char(string="Legend code")
