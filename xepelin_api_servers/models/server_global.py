# -*- coding: utf-8 -*-

import re
import logging
import requests
from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.addons.xepelin_movements.const import REGEX_ENTITIES_MX

_logger = logging.getLogger(__name__)


class ServerGlobal(models.Model):
    _name = 'server.global'
    _description = 'Xepelin Server Global'

    name = fields.Char(string="Name", copy=False)
    active = fields.Boolean(string="Active", default=True)
    test_mode = fields.Boolean(string="Test Mode", default=True)
    bo_host = fields.Char(string="Prod. BO Host",
                          help="Back Office production server")
    gb_host = fields.Char(string="Prod. GB Host",
                          help="Global XEPELIN production server")
    gb_token = fields.Char(string="Prod. GB Token",
                           help="Global XEPELIN production token", copy=False)
    test_bo_host = fields.Char(string="Test BO Host",
                               help="Back Office test server")
    test_gb_host = fields.Char(string="Test GB Host",
                               help="Global XEPELIN test server")
    test_gb_token = fields.Char(
        string="Test GB Token", help="Global XEPELIN test token", copy=False)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True)

    _sql_constraints = [
        ("company_id_unique", "unique (company_id)",
         "You can only add one global server configuration per company."),
        ("name_unique", "unique (name)", "The name must be unique."),
    ]

    def toggle_test_environment(self):
        for s in self:
            s.test_mode = not s.test_mode

    def _get_sever_params(self):
        if self.test_mode:
            host = self.test_gb_host
            token = self.test_gb_token
        else:
            host = self.gb_host
            token = self.gb_token

        return host, token

    def sanitize_payer_name(self, payer_name):
        payer_name = payer_name.replace(".","").replace(",","").upper().strip()
        payer_name = re.sub(REGEX_ENTITIES_MX, '', payer_name)

        return payer_name

    def search_all_partners(self, size=200, page=1):
        partner_obj = self.env['res.partner']
        host, token = self._get_sever_params()
        URL = "%s/api/backoffice/business" % (host)
        country_code = self.company_id.country_id.code
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer %s" % token,
        }
        params = {
            "page": page,
            "size": size,
            "country": country_code,
        }
        _logger.info('Searching for contacts in BO [page=%s, size=%s]' % (page, size))
        r = requests.get(URL, headers=headers, params=params)
        if r.ok:
            response_json = r.json()
            r_data = response_json.get("data", [])
            for r in r_data:
                try:
                    partner_id = partner_obj.search([('vat','=',r['identifier'])],limit=1)
                    if not partner_id:
                        partner_id.with_context(no_vat_validation=True).create({
                            "name": r['name'], 
                            "vat": r['identifier'], 
                            "country_id": self.company_id.country_id.id
                        })
                    else:
                        partner_id.with_context(no_vat_validation=True).write({
                            "name": r['name'], 
                            "country_id": self.company_id.country_id.id  
                        })
                except Exception as e:
                    _logger.exception('A problem occurred while creating/updating contacts. \n%s' % e)

            return True
        else:
            _logger.exception('A problem occurred while consulting contacts in BO')
            return False
        
    def search_partner_vat(self, payer_name):
        host, token = self._get_sever_params()
        URL = "%s/api/backoffice/business/" % (host)
        country_code = self.company_id.country_id.code
        headers = {
            "Content-Type": "application/json",
            "Country": country_code,
            "Authorization": "Bearer %s" % token,
        }
        payer_name_sanitize = self.sanitize_payer_name(payer_name)
        params = {
            "searchInput": payer_name_sanitize,
            "field": "name",
            "country": country_code,
        }
        
        _logger.info('Consulting RFC API for: "%s"' % payer_name_sanitize)
        r = requests.get(URL, headers=headers, params=params)
        if r.ok:
            response_json = r.json()
            r_data = response_json.get("data", [])
            if r_data:
                # Assumes no company has the same name than other **
                partner_vat = r_data[0].get("identifier", "")
                partner_name = r_data[0].get("name", "")
                _logger.info('RFC found for: "%s"' % partner_name)
                return partner_vat, partner_name
            else:
                _logger.warning('No RFC found for: "%s"' % payer_name_sanitize)
                return None, payer_name
        else:
            _logger.exception('A problem occurred while consulting the RFC for: "%s"' % payer_name_sanitize)
            return None, payer_name
    
    def search_partner_orderinvoices(self, partner_vat):
        host, token = self._get_sever_params()
        URL = f"{host}/api/backoffice/conciliation/orderinvoice/{partner_vat}/order/detailbyidentifier"
        headers = {
            "Content-Type": "application/json",
            "Country": self.company_id.country_id.code,
            "Authorization": "Bearer %s" % token,
        }
        
        _logger.info('Consulting orders for: "%s"' % partner_vat)
        r = requests.get(URL, headers=headers)
        if r.ok:
            data_json = r.json()
            orders = data_json.get("orders", [])
            _logger.info('%s Orders found for: "%s"' % (len(orders), partner_vat))
            return orders
        else:
            _logger.exception('A problem occurred while consulting the OrderInvoice for: "%s"' % partner_vat)
        
        return False
