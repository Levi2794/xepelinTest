import datetime
import sys
import logging

from pickle import TRUE
from odoo import fields,models
from ..services import get_wallet_client
from ..external.wallet_library.src import BadJsonReceivedException, InvalidBeneficiaryIdentifierException, WalletNotFoundException, UnknownTransactionApiException

_logger = logging.getLogger(__name__)

class XepelinDisburseOrder(models.Model):
    _name = 'xepelindisburseorder.disburse_order'
    _description = 'Disburse Order Request'

    # Details
    order_id = fields.Char(string='Order id', required=True)
    transaction_order_id = fields.Char(string='Transaction order id', required=True)

    product = fields.Char(required=True)
    segment = fields.Char(required=True)
    lifecycle_state = fields.Char(required=False)
    convention = fields.Char(required=True)
    operation_date = fields.Date(required=True)
    pay_date = fields.Date(required=True)

    # Disburse details
    beneficiary_name = fields.Char(string='Beneficiary name', required=True)
    bank_name = fields.Char(string='Bank name', required=True)
    beneficiary_account_number = fields.Char(string='Beneficiary account number', required=True)
    beneficiary_account_alias = fields.Char(string='Beneficiary account alias', required=True)
    beneficiary_identifier = fields.Char(string='Beneficiary identifier', required=True)
    reference = fields.Char(string='Payment reference', required=True)
    concept = fields.Char(string='Payment concept', required=True)
    amount_to_transfer = fields.Float('Total amount', required=True, tracking=True)

    # Tracking
    original_json = fields.Char('Original josn request', required=True)

    # relations
    invoices_id = fields.One2many('xepelindisburseorder.disburse_order_invoices', 'disburse_order_id')
    folios_id = fields.One2many('xepelindisburseorder.disburse_order_folios', 'disburse_order_id')
    business = fields.One2many('xepelindisburseorder.disburse_order_business', 'disburse_order_id')
    errors = fields.One2many('xepelindisburseorder.disburse_order_wallet_errors', 'disburse_order_id')

    currency = fields.Many2one('res.currency', string="Currency", required=False)
    country = fields.Many2one('res.country', string="Country", required=False)

    # aux
    status = fields.Char(
        selection=[
            ('TO_DISBURSE', 'Por dispersar'),
            ('DISBURSED', 'Dispersada'),
            ('IN_PROGRESS', 'Dispersion en progreso'),
            ('ERROR', 'Error'),
            ('REJECTED', 'Rechazada')
        ],
        string='Order state',
        default='TO_DISBURSE',
       
        required=True
    )

    source_account_number = fields.Char(string='Source account number', required=True)

    def _check_is_can_be_rejected(self):
        self.can_be_rejected = False
        if self.status == 'TO_DISBURSE':
            self.can_be_rejected = True

    can_be_rejected = fields.Boolean(compute=_check_is_can_be_rejected, readonly=True)

    def disburse_order(self):
        wallet_client = get_wallet_client()
        active_ids = self.env.context.get('active_ids', [])

        for id in active_ids:
            order = self.env["xepelindisburseorder.disburse_order"].sudo().search([
                ("id", "=", id)
            ], limit=1)
            if order is None or order.status != "TO_DISBURSE":
                continue

            errors_to_add = []
            business = order.business[0]
            current_date = datetime.date.today()
            
            try:
                disburse_body = {
                    "fromAccount": "TODO",
                    "payOrderRequests": [
                        {
                            "id": order.transaction_order_id,
                            "toAccount": order.beneficiary_account_number,
                            "amount": order.amount_to_transfer,
                            "concept": "concept",
                            "beneficiaryName": order.beneficiary_name,
                            "referenceNumber": "reference",
                            "beneficiaryIdentifier": order.beneficiary_identifier,
                        }
                    ]
                }
                wallet_client.create_cashout(disburse_body)
            except WalletNotFoundException:
                code = "WalletNotFoundException"
                errors_to_add.append(
                    (0, 0, { "code": code, "created_at": current_date })
                )
            except InvalidBeneficiaryIdentifierException:
                code = "InvalidBeneficiaryIdentifierException"
                errors_to_add.append(
                    (0, 0, { "code": code, "created_at": current_date })
                )
            except (UnknownTransactionApiException, BadJsonReceivedException) as e:
                code = type(e).__name__
                errors_to_add.append(
                    (0, 0, { "code": code, "created_at": current_date })
                )
            except:
                error = sys.exc_info()[0].__name__
                code = error
                _logger.error(error)
                errors_to_add.append(
                    (0, 0, { "code": code, "created_at": current_date })
                )
            
            if len(errors_to_add) > 0:
                order.update({ "errors": errors_to_add })


    def reject_order(self):
        self.write({
            'status': 'REJECTED'
        })