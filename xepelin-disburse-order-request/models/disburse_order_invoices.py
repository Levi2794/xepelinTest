import datetime
from pickle import TRUE
from odoo import fields,models
import logging
_logger = logging.getLogger(__name__)

class XepelinDisburseOrderInvoices(models.Model):
    _name = 'xepelindisburseorder.disburse_order_invoices'
    _description = 'Disburse Order Request Invoices'

    disburse_order_id = fields.Many2one('xepelindisburseorder.disburse_order', 'Disburse order id')

    invoice_id = fields.Integer(required=True)
