# -*- coding: utf-8 -*-

import logging
from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SearchOrderInvoice(models.TransientModel):
    _name = "search.orderinvoice.wizard"
    _description = "Search Order-Invoice"

    partner_ids = fields.Many2many("res.partner", string="Partners")

    def action_search(self):
        server_global_obj = self.env["server.global"]
        server_global_id = server_global_obj.search(
                [('company_id', '=', self.env.company.id)], limit=1)

        if not server_global_id:
            raise ValidationError(_('No connection to global server found.'))

        partner_count_total = len(self.partner_ids)
        partner_count = 0
        found_count = 0
        errors = []
        for partner in self.partner_ids:
            partner_count += 1
            _logger.info('BO-Querying Partner orders %s/%s' % (partner_count, partner_count_total))
            records = server_global_id.search_partner_orderinvoices(partner.vat)
            if records:
                rec_count = 0
                for rec in records:
                    try:
                        rec_count += 1
                        _logger.info('Creating/updating order %s/%s' % (rec_count, len(records)))
                        order_id = self._get_order(rec)
                        found_count =+ 1
                    except Exception as e:
                        errors.append(e)
                        _logger.exception('There was a problem getting the orders for: "%s"\n%s' % (partner.vat, e))

    def _get_order(self, values):
        order_obj = self.env["xepelin.order"]
        order_id = order_obj.search([('number','=',values['id'])])
        partner_id = self._get_partner(values['Business'])
        if not order_id:
            order_id = order_obj.create({
                "number": values['id'],
                "partner_id": partner_id.id,
                "order_type": values['orderType'],
                "status": values['status'],
                "status_reason": values.get('statusReason',''),
                #"date_order": values['createdAt'],
                "final_amount": values['OrderDetails'][0]['finalAmount'],
                "transfer": values['OrderDetails'][0]['transfer'],
                "retention": values['OrderDetails'][0]['retencion'],
                "retention_pct": values['OrderDetails'][0]['retentionPct'],
                "advance_payment": values['OrderDetails'][0]['anticipo'],
                "interest": values['OrderDetails'][0]['interes'],
                "base_rate": values['OrderDetails'][0]['tasaBase'],
                "operation_cost": values['OrderDetails'][0]['operationCost'],
                #"issued_date": values['OrderDetails'][0]['issuedDate'],
            })
        else:
            order_id.write({
                "order_type": values['orderType'],
                "partner_id": partner_id.id,
                "status": values['status'],
                "status_reason": values.get('statusReason',''),
                "final_amount": values['OrderDetails'][0]['finalAmount'],
                "transfer": values['OrderDetails'][0]['transfer'],
                "retention": values['OrderDetails'][0]['retencion'],
                "retention_pct": values['OrderDetails'][0]['retentionPct'],
                "advance_payment": values['OrderDetails'][0]['anticipo'],
                "interest": values['OrderDetails'][0]['interes'],
                "base_rate": values['OrderDetails'][0]['tasaBase'],
                "operation_cost": values['OrderDetails'][0]['operationCost'],
                #"issued_date": values['OrderDetails'][0]['issuedDate'],
                })

        self._get_discounts(order_id, values['Discounts'])
        self._get_invoices(order_id, values['OrderInvoices'])
        return order_id

    def _get_discounts(self, order_id, values):
        disc_obj = self.env["xepelin.order.discount"]
        for disc in values:
            disc_id = disc_obj.search([('order_id','=',order_id.id),('external_id','=',disc['id'])])
            if not disc_id:
                disc_id.create({
                    "reason": disc['reason'],
                    "external_id": disc['id'],
                    "amount": disc['amount'],
                    "order_id": order_id.id
                    })

    def _get_invoices(self, order_id, values):
        account_obj = self.env["account.move"]
        default_journal = account_obj._search_default_journal(['sale'])
        
        for invoice in values:
            account_id = account_obj.search([('name','=',invoice['Invoice']['folio']),('xepelin_id','=',invoice['invoiceId']),('journal_id','=',default_journal[0].id)])
            if not account_id:
                account_id = account_obj.create({
                    "move_type": 'out_invoice',
                    "journal_id": default_journal[0].id,
                    "xepelin_order_id": order_id.id,
                    "xepelin_id": invoice['invoiceId'],
                    "xepelin_status": invoice['status'],
                    #"invoice_date_due": invoice['expirationDate'],
                    "name": invoice['Invoice']['folio'],
                    "partner_id": order_id.partner_id.id,
                    #"invoice_date": invoice['Invoice']['createdAt'],
                    "xepelin_identifier": invoice['Invoice']['identifier'],
                    #"xepelin_issue_date": invoice['Invoice']['issueDate'],
                    "xepelin_tax_service": invoice['Invoice']['taxService'],
                    "xepelin_type": invoice['Invoice']['invoiceType'],
                    "xepelin_source": invoice['Invoice']['source'],
                    "xepelin_stakeholder_identifier": invoice['Invoice']['invoiceStakeholderIdentifier'],
                    'invoice_line_ids': [(0, 0, {
                        'name': 'XEPELIN Product',
                        'quantity': 1,
                        'price_unit': invoice['Invoice']['amount'],
                        'tax_ids': [(6, 0, [])],
                    })]
                })
                account_id.action_post()

        return True

    def _get_partner(self, values):
        country_obj = self.env["res.country"]
        partner_obj = self.env["res.partner"]
        partner_id = partner_obj.search([('vat','=',values['identifier'])],limit=1)
        if not partner_id:
            country_id = country_obj.search([('code','=',values['countryId'])],limit=1)
            partner_id = partner_obj.with_context(no_vat_validation=True).create({
                "name": values['name'],
                "vat": values['identifier'],
                "xepelin_id": values['id'],
                "country_id": country_id.id,
                "company_type": "company"
                })

            for user in values['Users']:
                partner_obj.with_context(no_vat_validation=True).create({
                    "name": user['name'],
                    "email": user['email'],
                    "phone": user['phone'],
                    "xepelin_id": user['id'],
                    "type": "contact",
                    "company_type": "person",
                    "parent_id": partner_id.id
                })
        else:
            partner_id.write({"name": values["name"]})
            for user in values['Users']:
                user_id = partner_obj.search([("parent_id","=", partner_id.id),('xepelin_id','=',user['id'])])
                if not user_id:
                    partner_obj.with_context(no_vat_validation=True).create({
                        "name": user['name'],
                        "email": user['email'],
                        "phone": user['phone'],
                        "xepelin_id": user['id'],
                        "type": "contact",
                        "company_type": "person",
                        "parent_id": partner_id.id
                    })
                else: user_id.write({
                        "name": user['name'],
                        "email": user['email'],
                        "phone": user['phone'],
                    })

        return partner_id
