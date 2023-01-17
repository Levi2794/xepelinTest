class AccountNotFoundForBusinessIdException(BaseException):
    def __init__(self, business_id):
        super().__init__(f"Account not found for business id '{business_id}")
