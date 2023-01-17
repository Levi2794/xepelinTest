import json

class CepNotFoundException(BaseException):
    def __init__(self, params):
        super().__init__(f"CEP not found. Params: {json.dumps(params)}")
