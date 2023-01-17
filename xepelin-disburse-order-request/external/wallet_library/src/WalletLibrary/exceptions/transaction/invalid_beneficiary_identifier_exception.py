class InvalidBeneficiaryIdentifierException(BaseException):
    def __init__(self, identifier):
        super().__init__(
            f"Trying to generate a cashout with an invalid beneficiary identifier: '{identifier}'")
