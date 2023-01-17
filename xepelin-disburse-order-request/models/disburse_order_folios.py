import datetime
from pickle import TRUE
from odoo import fields,models
import logging
_logger = logging.getLogger(__name__)

class XepelinDisburseOrderFolios(models.Model):
    _name = 'xepelindisburseorder.disburse_order_folios'
    _description = 'Disburse Order Request Folios'

    disburse_order_id = fields.Many2one('xepelindisburseorder.disburse_order', 'Disburse order id')

    folio_id = fields.Integer(required=True)
