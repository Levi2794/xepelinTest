class WalletNotFoundException(BaseException):
    def __init__(self, account_number) -> None:
        super().__init__(f"Wallet not found for account '{account_number}'")
