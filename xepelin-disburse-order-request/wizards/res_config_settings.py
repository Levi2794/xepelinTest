from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from ..config import default_config


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    wallet_url = fields.Char(
        string='Wallet Private key',
        config_parameter='xepelin_disburse_order_request.wallet_url',
        default=default_config["wallet"]["url"]
    )

    wallet_use_encryption = fields.Boolean(
        string='Wallet use encryption',
        config_parameter='xepelin_disburse_order_request.wallet_use_encryption',
    )

    wallet_private_key = fields.Char(
        string='Wallet Private key',
        config_parameter='xepelin_disburse_order_request.wallet_private_key',
        default=default_config["wallet"]["private_key"]
    )

    wallet_public_key = fields.Char(
        string='Wallet Private key',
        config_parameter='xepelin_disburse_order_request.wallet_public_key',
        default=default_config["wallet"]["public_key"]
    )

    wallet_passphrase = fields.Char(
        string='Wallet Private key',
        config_parameter='xepelin_disburse_order_request.wallet_passphrase',
        default=default_config["wallet"]["passphrase"]
    )

    server_global_auth_token = fields.Char(
        string='Server Global Token',
        config_parameter='xepelin_disburse_order_request.server_global_auth_token',
        default=default_config["server_global"]["token"]
    )

    server_global_domain = fields.Char(
        string='Server Global URL',
        config_parameter='xepelin_disburse_order_request.server_global_domain',
        default=default_config["server_global"]["url"]
    )

    server_global_update_invoice_path = fields.Char(
        string='Server Global Update Invoice URL PATH',
        config_parameter='xepelin_disburse_order_request.server_global_update_invoice_path',
        default=default_config["server_global"]["update_invoice_path"]
    )
