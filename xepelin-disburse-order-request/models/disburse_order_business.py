import datetime
from pickle import TRUE
from odoo import fields,models
import logging
_logger = logging.getLogger(__name__)

class XepelinDisburseOrderBusiness(models.Model):
    _name = 'xepelindisburseorder.disburse_order_business'
    _description = 'Disburse Order Request Business'

    disburse_order_id = fields.Many2one('xepelindisburseorder.disburse_order', 'Disburse order id')

    name = fields.Char(required=True)
    identifier= fields.Char(required=True)
