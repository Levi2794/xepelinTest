# -*- coding: utf-8 -*-

import datetime

from odoo import fields, models
from odoo.exceptions import ValidationError

class PaymentPayment(models.Model):
    _name = 'xepelin.payment.payment'
    _description = 'Payments'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    __states = [
    ('rejected', 'Rejected'),
    ('waiting_area_approval', 'Waiting For Area Approval'),
    ('waiting_budget_approval', 'Waiting For Budget Approval'),
    ('waiting_accounting_approval', 'Waiting For Accounting Approval'),
    ('waiting_treasury_approval', 'Waiting For Treasury Approval'),
    ('approved', 'Approved'),
    ('paid', 'Paid'),
    ]


    beneficiary_name = fields.Char(string='Beneficiary name', tracking=True, required=True)
    bank_id = fields.Many2one('res.bank', string="Bank")
    beneficiary_account_number = fields.Char(string='Beneficiary account number', tracking=True, required=True)
    beneficiary_account_alias = fields.Char(string='Beneficiary account alias', tracking=True)
    beneficiary_identifier = fields.Char(string='Beneficiary identifier', tracking=True, required=True)
    reference = fields.Char(string='Payment reference', tracking=True)
    concept = fields.Char(string='Payment concept', tracking=True, required=True)
    subtotal_amount = fields.Float('Subtotal amount', required=True, tracking=True)
    tax_iva_amount = fields.Float('Tax amount', required=True, tracking=True)
    rent_tax_iva_amount = fields.Float('Rent tax iva amount', required=True, tracking=True)
    rent_tax_isr_amount = fields.Float('Rent tax isr amount', required=True, tracking=True)
    total_amount = fields.Float('Total amount', required=True, tracking=True)
    exchange_rate_usd = fields.Float('Exchange rate to usd', required=True, tracking=True)
    total_amount_usd = fields.Float('Total amount usd', required=True, tracking=True)
    state = fields.Selection(selection=__states, string='State', required=True, copy=False, tracking=True,
        default=__states[1][0])
    distribution_funds = fields.Char(string='Distribution and funds', tracking=True)
    rights_other_contributions = fields.Char(string='Rights and other contributions', tracking=True)

    def _check_is_group_area_approver(self):
        result = False
        max_per_currency = self.env['xepelin.payment.max.per.currency'].sudo().search([('currency_id', '=', self.currency_id.id)], limit=1)

        group_supervisor = 'xepelin_payment.group_%s_supervisor' % self.area_id.code
        if self.env.user.has_group(group_supervisor) == True:
            result = True

        group_analyst = 'xepelin_payment.group_%s_analyst' % self.area_id.code
        if self.total_amount < max_per_currency.amount and self.env.user.has_group(group_analyst) == True:
            result = True

        return result

    def _check_is_group_approver(self):
        self.is_group_approver = False
        if self.state == 'waiting_area_approval': 
            self.is_group_approver = self._check_is_group_area_approver()

        if self.state == 'waiting_budget_approval':
            self.is_group_approver = self.env.user.has_group('xepelin_payment.group_budget')

        if self.state == 'waiting_accounting_approval':
            self.is_group_approver = self.env.user.has_group('xepelin_payment.group_accounting')
        
        if self.state == 'waiting_treasury_approval':

            if self.env.user.has_group('xepelin_payment.group_treasury_supervisor') or self.env.user.has_group('xepelin_payment.group_treasury_analyst'):
                self.is_group_approver = True

            max_per_currency = self.env['xepelin.payment.max.per.currency'].sudo().search([('currency_id', '=', self.currency_id.id)], limit=1)
            if max_per_currency.amount > 0 and self.env.user.has_group('xepelin_payment.group_treasury_supervisor') == False:
                if self.total_amount >= max_per_currency.amount and self.env.user.has_group('xepelin_payment.group_treasury_analyst') == True:
                    self.is_group_approver = False
                
    def _check_is_payer_group(self):
        self.is_payer_group = False        
        if self.state == 'approved' and (self.env.user.has_group('xepelin_payment.group_treasury_supervisor') or self.env.user.has_group('xepelin_payment.group_treasury_analyst')) :
            self.is_payer_group = True

    is_group_approver = fields.Boolean(compute=_check_is_group_approver, readonly=True)
    is_payer_group = fields.Boolean(compute=_check_is_payer_group, readonly=True)
    document_description = fields.Char(string='Document description', tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency", required=True)
    country_id = fields.Many2one('res.country', string="Country", required=True)
    creation_date = fields.Date(required=True, string="Creation date", default= datetime.datetime.now())
    beneficiary_address = fields.Char(string='Beneficiary address')
    bank_city = fields.Char(string='Bank city')
    bank_state = fields.Char(string='Bank state')
    bank_country = fields.Char(string='Bank country')
    aba_swift = fields.Char(string='Aba/Swift')
    area_id = fields.Many2one('xepelin.payment.area', string="Area", required=True)
    invoice_link = fields.Char(string='Invoice link')
    comment = fields.Char(string='Comment')
    invoice_date = fields.Date(string="Invoice date", default= datetime.datetime.now())
    requesting_user = fields.Char(string='Requesting user')

    remove_edit_css = fields.Html(
        sanitize=False,
        compute='remove_edit_button',
        store=False,
    )

    def remove_edit_button(self):
        for rec in self:
            # To Remove Edit Option
            if self.env.user.has_group('xepelin_payment.group_admin') == False :
                rec.remove_edit_css ='<style>.o_form_button_edit {display: none !important;}</style>'
            else:
                rec.remove_edit_css = False


    def __searchStateIndex(self, value): 
        index = 0
        for state in self.__states:
            if state[0] == value:
                return index
            index = index + 1
        return None
        
    def __getNextState(self):
        current_state_index = self.__searchStateIndex(self.state)
        return self.__states[current_state_index + 1][0]

    def approve_payment_request(self):
        self.write({
            'state': self.__getNextState()
        })
                     
    def paid_payment_request(self):
        self.write({
            'state': 'paid'
        })
    
    def reject_payment_request(self):
        self.write({
            'state': 'rejected'
        })

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, f"PAY-{rec.creation_date}"))
        return result
    
    def download_file(self):
        if self.env.user.has_group('xepelin_payment.group_treasury_supervisor') or self.env.user.has_group('xepelin_payment.group_treasury_analyst') :
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            selected_ids = self.env.context.get('active_ids', [])

            # prepare download url
            download_url = '/download_file'
            # download
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url) + "?ids=" + ",".join(map(str,selected_ids)),
                "target": "self",
            }

    def write(self, values):
        self.check_payment_status(values)
        res = super(PaymentPayment, self).write(values)
        return res

    def check_payment_status(self, values):
        if 'state' not in values and self.state in ['approved', 'paid']:
            raise ValidationError("You cannot edit an already approved request")