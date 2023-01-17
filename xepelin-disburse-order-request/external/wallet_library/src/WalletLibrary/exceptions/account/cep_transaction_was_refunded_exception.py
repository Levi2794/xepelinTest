import json


class CepTransactionWasRefundedException(BaseException):
    def __init__(self, params):
        super().__init__(
            f"No CEP available, verification transaction was refunded. Params: {json.dumps(params)}")
