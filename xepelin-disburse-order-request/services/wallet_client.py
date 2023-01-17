import os
from odoo.http import request
from ..external.wallet_library.src.WalletLibrary import WalletClient


def get_wallet_client():
    env = request.env
    params = env['ir.config_parameter'].sudo()

    url = params.get_param("xepelin_disburse_order_request.wallet_url")
    use_encryption = params.get_param("xepelin_disburse_order_request.wallet_use_encryption")
    private_key = params.get_param("xepelin_disburse_order_request.wallet_private_key")
    public_key = params.get_param("xepelin_disburse_order_request.wallet_public_key")
    passphrase = params.get_param("xepelin_disburse_order_request.wallet_passphrase")

    return WalletClient(
        url,
        use_encryption=use_encryption,
        private_key=private_key,
        passphrase=passphrase,
        public_key=public_key
    )
