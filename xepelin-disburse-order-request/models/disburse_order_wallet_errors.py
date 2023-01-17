import datetime
from pickle import TRUE
from odoo import fields,models
import logging
_logger = logging.getLogger(__name__)

class XepelinDisburseOrderWalletErrors(models.Model):
    _name = 'xepelindisburseorder.disburse_order_wallet_errors'
    _description = 'Disburse Order Request Wallet errors'

    disburse_order_id = fields.Many2one('xepelindisburseorder.disburse_order', 'Disburse order id')

    code = fields.Char(required=True)
    description = fields.Char(required=False)
    created_at = fields.Date('Create Date', readonly=True)
