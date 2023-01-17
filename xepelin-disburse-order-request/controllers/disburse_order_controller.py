# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import request, Response
from ..services import DisburseOrderService
from ..exceptions import OrderAlreadyExists, AccountNumberSourceDoesNotExist
import logging

_logger = logging.getLogger(__name__)


class DisburseOrderController(http.Controller):
    _service = DisburseOrderService()

    @http.route("/disburse/order/status", type="json", auth="public", methods=["POST"], csrf=False)
    def post_update_order_sns(self):
        body = json.loads(request.jsonrequest["Message"])

        if body["eventType"] != "PAY_ORDER_STATUS":
            status = 400
            response = "Event type is not \"PAY_ORDER_STATUS\""
            return {
                "status": status,
                "response": response,
            }

        transaction_order_id = body["id"]
        status = body["status"]
        errorTypeId = body["errorTypeId"]
        errorDescription = body["errorDescription"]

        response = self._service.update_invoice_status(
            transaction_order_id, status, errorTypeId, errorDescription)

        return {
            "status": status,
            "response": response,
        }

    @http.route("/disburse/order/callback", type="json", auth="public", methods=["POST"], csrf=False)
    def post_disburse_order(self):
        status = 200
        response = None

        try:
            order_id = request.jsonrequest["order_id"]

            exists = request.env["xepelindisburseorder.disburse_order"].sudo().search([
                ("order_id", "=", order_id)
            ], limit=1)

            if exists:
                raise OrderAlreadyExists()

            response = self._service.post_disburse_order(request.jsonrequest)
        except OrderAlreadyExists:
            status = 409
            response = "Order with id \"" + \
                str(order_id) + "\" already exists."
        except AccountNumberSourceDoesNotExist as e:
            status = 409
            response = str(e)
            _logger.error(response) 

        return {
            "status": status,
            "response": response,
        }
