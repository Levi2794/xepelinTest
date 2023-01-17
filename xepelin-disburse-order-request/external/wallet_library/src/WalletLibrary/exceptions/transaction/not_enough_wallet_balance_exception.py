class NotEnoughWalletBalanceException(BaseException):
    def __init__(self, account_number):
        super().__init__(
            f"Wallet for accountId {account_number} does not have enough balance to complete the order.")
