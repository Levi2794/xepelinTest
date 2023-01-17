import os
import requests
import logging
from odoo.http import request
from ..config import default_config

_logger = logging.getLogger(__name__)


class ServerGlobal:
    def __init__(self):
        env = request.env
        params = env['ir.config_parameter'].sudo()

        self.url = params.get_param("xepelin_disburse_order_request.server_global_domain")
        self.update_invoice_path = params.get_param("xepelin_disburse_order_request.server_global_update_invoice_path")
        self.token = params.get_param("xepelin_disburse_order_request.server_global_auth_token")

    def _secure_request(self, url, method="GET", body={}, headers={}):
        return requests.request(method, url, json=body, headers=headers)

    def update_invoice_status(self, order_id, invoice_id, status):
        url = self.url + "/" + self.update_invoice_path
        body = {
            "orderId": order_id,
            "invoiceId": invoice_id,
            "status": status
        }
        method = "POST"
        headers = {}

        if self.token is not None and self.token is not False:
            headers["Authorization"] = "Bearer " + self.token

        return self._secure_request(
            url=url,
            body=body,
            method=method,
            headers=headers
        )
