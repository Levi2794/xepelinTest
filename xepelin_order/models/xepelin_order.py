# -*- coding: utf-8 -*-

from odoo import _, api, fields, models


class Order(models.Model):
    _name = "xepelin.order"
    _description = "Xepelin Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Folio", required=True, readonly=True, default=lambda self: _("New"))
    number = fields.Char(string="Number", tracking=True, copy=False, required=True)
    business_id = fields.Char(string="Business ID", tracking=True, copy=False)
    order_type = fields.Char(string="Order type", tracking=True, copy=False, required=True)
    status = fields.Char(string="Status", tracking=True, copy=False)
    status_reason = fields.Char(string="Status Reason", tracking=True, copy=False)
    date_order = fields.Datetime(string="Date Order")
    partner_id = fields.Many2one("res.partner", string="Partner", ondelete='restrict')
    partner_vat = fields.Char(string="Partner ID", related="partner_id.vat")
    
    #OrderDetails
    final_amount = fields.Monetary(string="Final amount")
    transfer = fields.Monetary(string="Transfer")
    retention = fields.Monetary(string="Retention")
    retention_pct = fields.Float(string="Retention PCT")
    advance_payment = fields.Monetary(string="Advance payment")
    interest = fields.Monetary(string="Interest")
    base_rate = fields.Float(string="Base rate")
    operation_cost = fields.Monetary(string="Operation cost")
    issued_date = fields.Datetime(string="Issued date")

    discount_ids = fields.One2many("xepelin.order.discount", "order_id", string="Discounts")
    invoice_ids = fields.One2many("account.move", "xepelin_order_id", string="Related invoices")
    company_id = fields.Many2one("res.company", string="Company", ondelete='restrict', default=lambda self: self.env.company)
    currency_id = fields.Many2one("res.currency",string="Currency", ondelete='restrict', default=lambda self: self.env.user.company_id.currency_id.id)
    invoice_count = fields.Integer(compute="_compute_related_count", string="Invoice Count")
    discount_count = fields.Integer(compute="_compute_related_count", string="Discount Count")
    
    def bo_order_link(self):
        params = self.env["ir.config_parameter"].sudo()
        bo_url = params.get_param("xepelin_movement.back_office_mx_url")
        return {
            "name": _("BO Order"),
            "type": "ir.actions.act_url",
            "url": f"{bo_url}/orders/{self.number}",
            "target": "new",
        }

    def _compute_related_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)
            rec.discount_count = len(rec.discount_ids)

    def action_view_invoices(self):
        invoices = self.mapped('invoice_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_move_type': 'out_invoice',
            'default_xepelin_order_id': self.id,
            'default_partner_id': self.partner_id.id,
            'default_user_id': self.env.uid,
        }

        action['context'] = context
        return action

    def action_view_discounts(self):
        discounts = self.mapped('discount_ids')
        action = self.env["ir.actions.actions"]._for_xml_id("xepelin_order.xepelin_order_discount_action")
        if len(discounts) > 1:
            action['domain'] = [('id', 'in', discounts.ids)]
        elif len(discounts) == 1:
            form_view = [(self.env.ref('xepelin_order.xepelin_order_discount_view_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = discounts.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_order_id': self.id,
        }

        action['context'] = context
        return action

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code("xepelin.order") or _("New")

        res = super(Order, self).create(vals)
        return res
