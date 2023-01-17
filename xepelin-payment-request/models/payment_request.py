import datetime
from pickle import TRUE
from odoo import fields,models
import logging
_logger = logging.getLogger(__name__)


class XepelinPaymentRequestPaymentRequest(models.Model):
    _name = 'xepelinpaymentrequest.paymentrequest'
    _description = 'Payment Resquest'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    beneficiary_name = fields.Char(string='Beneficiary name', tracking=True, required=True)
    bank_name = fields.Char(string='Bank name', tracking=True, required=True)
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
    state = fields.Selection(selection=[
        ('rejected', 'Rejected'),
        ('waiting_budget_approval', 'Waiting For Budget Approval'),
        ('waiting_accounting_approval', 'Waiting For Accounting Approval'),
        ('waiting_treasury_approval', 'Waiting For Treasury Approval'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
    ], string='State', required=True, readonly=True, copy=False, tracking=True,
        default='waiting_budget_approval')
    distribution_funds = fields.Char(string='Distribution and funds', tracking=True)
    rights_other_contributions = fields.Char(string='Rights and other contributions', tracking=True)

    def _check_is_group_approver(self):

        self.is_group_approver = False
        if self.state == 'waiting_budget_approval':
            self.is_group_approver = self.env.user.has_group('xepelin-payment-request.group_budget')

        if self.state == 'waiting_accounting_approval':
            self.is_group_approver = self.env.user.has_group('xepelin-payment-request.group_accounting')
        
        if self.state == 'waiting_treasury_approval':

            if self.env.user.has_group('xepelin-payment-request.group_treasury_supervisor') or self.env.user.has_group('xepelin-payment-request.group_treasury_analyst'):
                self.is_group_approver = True

            max_per_currencies = self.env['xepelinpaymentrequest.maxpercurrency'].sudo().search([('currency_id', '=', self.currency_id.id)])

            if len(max_per_currencies) > 0 and self.env.user.has_group('xepelin-payment-request.group_treasury_supervisor') == False:
                max_per_currency = max_per_currencies[0]
                if self.total_amount > max_per_currency.amount and self.env.user.has_group('xepelin-payment-request.group_treasury_analyst') == True:
                    self.is_group_approver = False
                
    def _check_is_payer_group(self):
        self.is_payer_group = False        
        if self.state == 'approved' and (self.env.user.has_group('xepelin-payment-request.group_treasury_supervisor') or self.env.user.has_group('xepelin-payment-request.group_treasury_analyst')) :
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
    area = fields.Char(string='Area')
    invoice_link = fields.Char(string='Invoice link')
    comment = fields.Char(string='Comment')
    invoice_date = fields.Date(string="Invoice date", default= datetime.datetime.now())
    requesting_user = fields.Char(string='Requesting user')

    def approve_payment_request(self):
        if self.state == 'waiting_budget_approval':
            self.write({
                'state': 'waiting_accounting_approval'
            })
            return

        if self.state == 'waiting_accounting_approval':
            self.write({
                'state': 'waiting_treasury_approval'
            })
            return
        
        if self.state == 'waiting_treasury_approval':
            self.write({
                'state': 'approved'
            }) 
            return     
                     
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
        if self.env.user.has_group('xepelin-payment-request.group_treasury_supervisor') or self.env.user.has_group('xepelin-payment-request.group_treasury_analyst') :
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            selected_ids = self.env.context.get('active_ids', [])

            # prepare download url
            download_url = '/download_file'
            # download
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url) + "?ids=" + ",".join(map(str,selected_ids)),
                "target": "self",
            }

