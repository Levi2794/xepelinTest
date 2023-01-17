import dateutil.parser
import json
import logging
from odoo.http import request, Response
from .server_global import ServerGlobal
from ..exceptions import AccountNumberSourceDoesNotExist

_logger = logging.getLogger(__name__)


class DisburseOrderService:
    @staticmethod
    def _get_currency(currency):
        response = request.env['res.currency'].sudo().search([
            '|',
            '|',
            ('name', '=', currency),
            ('symbol', '=ilike', '%' + currency + '%'),
            ('full_name', '=ilike', '%' + currency + '%')
        ], limit=1)
        if response is not None:
            return response["id"]

    @staticmethod
    def _get_country(country):
        response = request.env['res.country'].sudo().search([
            ('code', '=', country),
        ], limit=1)
        if response is not None:
            return response["id"]

    def update_invoice_status(self, transaction_order_id, disbursement_status, errorTypeId, errorDescription):
        _server_global = ServerGlobal()
        model = request.env["xepelindisburseorder.disburse_order"].sudo().search([
            ("transaction_order_id", "=", transaction_order_id)
        ], limit=1)

        if not model:
            return {
                "response": "No model found"
            }
        invoices_id = list(
            map(lambda invoice: invoice["invoice_id"], model.invoices_id))
        order_id = model.order_id
        status = model.status
        if disbursement_status == "COMPLETED":
            status = "DISBURSED" 
        elif disbursement_status == "IN_PROGRESS":
            status = "IN_PROGRESS"
        elif disbursement_status == "FAILED":
            status = "ERROR" 
            request.env['xepelindisburseorder.disburse_order_wallet_errors'].sudo().create({
                "disburse_order_id": model.id,
                'code': errorTypeId,
                'description': errorDescription
            })
        else:
            _logger.error("The disbursement status %s is not valid" % disbursement_status)

        model.update({"status": status})      
        for invoice_id in invoices_id:
            _server_global.update_invoice_status(order_id, invoice_id, status)

        return invoices_id

    def _get_source_account_number(self, country_id, product):
        response = request.env['xepelindisburseorder.disburse_order_account_product'].sudo().search([
            ('product', '=', product),
            ('country.id', '=', country_id),
        ])
        if response["account_number"] == False:
            message = "There is no account number assigned. product %s, country %s." % (product, country_id)
            raise AccountNumberSourceDoesNotExist(message)

        return response["account_number"] 

    def post_disburse_order(self, body):
        response = []

        # Global data
        order_id = body["order_id"]
        business_data = body["business"]
        segment = business_data["segment"]
        lifecycle_state = business_data["lifecycle_state"]
        convention = business_data["convention"]

        for operation in body["operations"]:
            provider = operation["provider"]
            bank_data = provider["bank"]
            transaction_order_id = operation["id"]

            # Operation data
            country = self._get_country(operation["country_id"])
            currency = self._get_currency(operation["currency"])

            product = operation["product"]
            operation_date = dateutil.parser.isoparse(
                operation["operation_date"])
            pay_date = dateutil.parser.isoparse(operation["pay_date"])

            # Disbursement data
            bank_name = bank_data["bank_name"]
            beneficiary_name = bank_data["beneficiary_name"]
            beneficiary_account_number = bank_data["account_number"]
            beneficiary_account_alias = bank_data["beneficiary_alias"]
            beneficiary_identifier = provider["identifier"]
            concept = operation["product"]
            amount_to_transfer = operation["amount_to_transfer"]

            # Relational data
            invoices_id = list(map(lambda invoice: (
                0, 0, {"invoice_id": invoice}), operation["invoices_id"]))
            folios_id = list(map(lambda invoice: (
                0, 0, {"folio_id": invoice}), operation["folios_id"]))

            reference = ""
            original_json = json.dumps(body)

            source_account_number = self._get_source_account_number(country, product)

            operation = request.env["xepelindisburseorder.disburse_order"].sudo().create({
                "order_id": order_id,
                "transaction_order_id": transaction_order_id,
                "country": country,
                "currency": currency,
                "product": product,
                "segment": segment,
                "lifecycle_state": lifecycle_state,
                "convention": convention,
                "operation_date": operation_date,
                "pay_date": pay_date,
                "beneficiary_name": beneficiary_name,
                "bank_name": bank_name,
                "source_account_number": source_account_number,
                "beneficiary_account_number": beneficiary_account_number,
                "beneficiary_account_alias": beneficiary_account_alias,
                "beneficiary_identifier": beneficiary_identifier,
                "reference": reference,
                "concept": concept,
                "amount_to_transfer": amount_to_transfer,

                "invoices_id": invoices_id,
                "folios_id": folios_id,
                "business": [
                    (0, 0, {
                        "name": business_data["name"],
                        "identifier": business_data["identifier"],
                    })
                ],

                "original_json": original_json,
            })

            response.append(operation)

        return response
