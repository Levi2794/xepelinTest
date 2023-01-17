# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"
    
    xepelin_order_id = fields.Many2one("xepelin.order", string="Order", ondelete='restrict')
    xepelin_id = fields.Char(string="Xepelin BO-ID")
    xepelin_identifier = fields.Char(string="Xepelin Identifier")
    xepelin_issue_date = fields.Char(string="Xepelin Issue Date")
    xepelin_tax_service = fields.Char(string="Xepelin Tax Service")
    xepelin_type = fields.Char(string="Xepelin Type")
    xepelin_stakeholder_identifier = fields.Char(string="Xepelin Stakeholder Identifier")
    xepelin_source = fields.Char(string="Xepelin Source")
    xepelin_status = fields.Char(string="Xepelin Status")
