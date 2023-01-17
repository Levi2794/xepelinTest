# -*- coding: utf-8 -*-

import datetime
from odoo import http
from odoo.http import request
import logging
_logger = logging.getLogger(__name__)


BENEFICIARY_NAME_LENGTH = 40
NAME_CURRENCIES = ['CLP', 'MXN', 'USD']
class ValidationError(Exception):
  pass

class PaymentRequestController(http.Controller):
    @http.route("/payment", type='json', auth="public", methods=['POST'], csrf=False)
    def post_paymnet_request(self):
      status = 200
      errors = []
      try:

        beneficiary_name = _get_dynamic_key_from_input(request.jsonrequest, 'beneficiaryName')
        if len(beneficiary_name) > BENEFICIARY_NAME_LENGTH:
          message = 'The name of the beneficiary exceeds 40 characters. value = %s' % beneficiary_name
          _logger.error(message)
          errors.append(message)

        country_code = _get_dynamic_key_from_input(request.jsonrequest, 'country')
        country = request.env['res.country'].sudo().search([('code', '=', country_code)], limit=1)
        if country.id == False:
          message = "Country %s does not exist" % country_code
          _logger.error(message)
          errors.append(message)

        bank_name = _get_dynamic_key_from_input(request.jsonrequest, 'bankName')
        bank = request.env['xepelin.payment.bank'].searchByName(bank_name)
        bank_id = None
        if bank == None:
          if country_code == 'CL' and currency_name == 'CLP':
            message = "Bank %s does not exist for country %s" % (bank_name, country_code)
            _logger.error(message)
            _logger.error("The bank is required for payments with currency %s in the country %s", (currency_name, country_code))
            errors.append(message)
        else:
         bank_id = bank['id']
        
        name_area = _get_dynamic_key_from_input(request.jsonrequest, 'area')
        area = request.env['xepelin.payment.area'].searchAreaByName(name_area)
        if area == None:
          message = "Area %s does not exist" % name_area
          _logger.error(message)
          errors.append(message)

        currency_name = _get_dynamic_key_from_input(request.jsonrequest, 'currency')
        if currency_name not in NAME_CURRENCIES:
          message = "Currency %s does not valid" % currency_name
          _logger.error(message)
          errors.append(message)
        currency = request.env['res.currency'].sudo().search([('name', '=', currency_name)], limit=1)

        beneficiary_account_number = _get_dynamic_key_from_input(request.jsonrequest, 'beneficiaryAccountNumber')
        if(currency_name == 'CLP' and country_code == 'CL' and len(beneficiary_account_number) > 12) or (currency_name == 'MXN' and country_code == 'MX' and len(beneficiary_account_number) != 18):
          message = "Bank account %s is invalid for country %s" % (beneficiary_account_number, country_code)
          _logger.error(message)
          errors.append(message)

        total_amount = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'totalAmount'))
        if float(total_amount) <= 0:
          message = "The amount must be greater than 0"
          _logger.error(message)
          errors.append(message)

        beneficiary_identifier = _get_dynamic_key_from_input(request.jsonrequest, 'beneficiaryIdentifier')
        concept = _get_dynamic_key_from_input(request.jsonrequest, 'concept')
        beneficiary_account_alias = _get_dynamic_key_from_input(request.jsonrequest, 'beneficiaryAccountAlias')
        reference = _get_dynamic_key_from_input(request.jsonrequest, 'reference')
        subtotal_amount = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'subtotalAmount'))
        tax_iva_amount = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'taxIvaAmount'))
        rent_tax_iva_amount = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'rentTaxIvaAmount'))
        rent_tax_isr_amount = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'rentTaxIsrAmount'))
        exchange_rate_usd = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'exchangeRateUsd'))
        total_amount_usd = _format_amount(_get_dynamic_key_from_input(request.jsonrequest, 'totalAmountUsd'))
        distribution_funds = _get_dynamic_key_from_input(request.jsonrequest, 'distributionFunds')
        rights_other_contributions = _get_dynamic_key_from_input(request.jsonrequest, 'rightsOtherContributions')
        document_description = _get_dynamic_key_from_input(request.jsonrequest, 'documentDescription')
        beneficiary_address = _get_dynamic_key_from_input(request.jsonrequest, 'beneficiaryAddress')
        bank_city = _get_dynamic_key_from_input(request.jsonrequest, 'bankCity')
        bank_state = _get_dynamic_key_from_input(request.jsonrequest, 'bankState')
        bank_country = _get_dynamic_key_from_input(request.jsonrequest, 'bankCountry')
        aba_swift = _get_dynamic_key_from_input(request.jsonrequest, 'abaSwift')
        invoice_link = _get_dynamic_key_from_input(request.jsonrequest, 'invoiceLink')
        invoice_date = _parse_date(_get_dynamic_key_from_input(request.jsonrequest, 'invoiceDate'))
        comment = _get_dynamic_key_from_input(request.jsonrequest, 'comment')
        requesting_user = _get_dynamic_key_from_input(request.jsonrequest, 'requestingUser')

        if len(errors) > 0:
          raise ValidationError
        
        request.env['xepelin.payment.payment'].sudo().create({
          'beneficiary_name': beneficiary_name,
          'bank_id': bank_id,
          'beneficiary_account_number': beneficiary_account_number,
          'beneficiary_account_alias': beneficiary_account_alias,
          'beneficiary_identifier': beneficiary_identifier,
          'reference': reference,
          'concept': concept,
          'subtotal_amount': subtotal_amount,
          'tax_iva_amount': tax_iva_amount,
          'rent_tax_iva_amount': rent_tax_iva_amount,
          'rent_tax_isr_amount': rent_tax_isr_amount,
          'total_amount': total_amount,
          'exchange_rate_usd': exchange_rate_usd,
          'total_amount_usd': total_amount_usd,
          'distribution_funds': distribution_funds,
          'rights_other_contributions': rights_other_contributions,
          'document_description': document_description,
          'currency_id': currency.id,
          'beneficiary_address': beneficiary_address,
          'bank_city': bank_city,
          'bank_state': bank_state,
          'bank_country': bank_country,
          'aba_swift': aba_swift,
          'area_id': area['id'],
          'invoice_link': invoice_link,
          'invoice_date': invoice_date,
          'comment': comment,
          'country_id': country.id,
          'requesting_user': requesting_user
        })

      except ValidationError:
        status = 400
      except Exception as e:
        _logger.error(str(e))
        status = 500

      return {"status": status }



def _get_dynamic_key_from_input(json, key):
  data = json['event']['workflow_step']['inputs']

  if key in data:
    return data[key]['value']
  return None

def _format_amount(value):
  if type(value) == str:
    return value.replace(',','.')
  return 0

def _parse_date(value):
  invoice_date = None
  try:
    invoice_date = datetime.datetime.strptime(value, '%d/%m/%Y')
  except:
    _logger.error("An error occurred when parsing the date. value = %s", value)
  return invoice_date
