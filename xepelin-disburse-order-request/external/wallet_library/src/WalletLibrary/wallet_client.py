"""Wallet Client."""

from .clients.account.account_api_client import AccountApiClient
from .clients.bbva.bbva_api_client import BbvaApiClient
from .clients.transaction.transaction_api_client import TransactionApiClient
from .clients.wallet.wallet_api_client import WalletApiClient


class WalletClient:
    """Wallet client."""

    def __init__(self, base_url, private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """WalletClient constructor.

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.
        """
        self.account_api_client = AccountApiClient(
            base_url, private_key, passphrase, public_key, use_encryption)
        self.bbva_api_client = BbvaApiClient(
            base_url, private_key, passphrase, public_key, use_encryption)
        self.transaction_api_client = TransactionApiClient(
            base_url, private_key, passphrase, public_key, use_encryption)
        self.wallet_api_client = WalletApiClient(
            base_url, private_key, passphrase, public_key, use_encryption)

    def create_wallet(self, payload):
        """Wallet creation endpoint.

        Args:
            payload (dict): {
                businessId: int, # id of the business that will own the new wallet.
                alias: str, # alias for the wallet. Basically, the name of the wallet.
                countryId: str, # valid ISO-3301 Alpha-2 country code for the wallet.
                identifier: str, # owner's identifier.
            }

        Raises:
            InvalidIdentifierException: owners identifier is not valid.
            UnknownWalletApiException: There was a problem communicating with Wallet's Wallet API.

        Returns:
            dict: {
                id: str, # id of the newly create wallet.
                businessId: int, # id of the business who owns the newly created wallet.
                accountNumber: str, # account number of the new wallet.
                providerId: str, # provider id associated to the new Wallet, e.g. STP.
                countryId: str, # valid ISO-3301 Alpha-2 country code of the new wallet.
                identifier: str, # wallet owner's identifier.
                alias: str, # wallet name.
                createdAt: str, # date and time of creation.
                updatedAt: str, # date and time of last update.
            }
        """
        return self.wallet_api_client.create_wallet(payload)

    def get_accounts_by_business_id(self, business_id):
        """Retrieves all wallets associated with a given business id.

        Args:
            business_id (int): business id.

        Raises:
            AccountNotFoundForBusinessIdException: no wallets found for the given business id.
            UnknownWalletApiException: There was a problem communicating with Wallet's Wallet API.

        Returns:
            list: [ # list of the wallets associated with the provided business id.
                {
                    businessId: int, # id of the business who owns the wallet.
                    accountNumber: str, # account number of the wallet.
                    alias: str, # name of the wallet.
                    bankName: str, # name of the bank associated with the wallet.
                },
                ...
            ]
        """
        return self.wallet_api_client.get_accounts_by_business_id(business_id)

    def get_account_for_business_by_account_number(self, business_id, account_number):
        """Retrieves a particular wallet for a business id.

        Args:
            business_id (int): business id who owns the wallet.
            account_number (str): account number of the wallet.

        Raises:
            AccountNotFoundForBusinessIdException: The account was not found.
            UnknownWalletApiException: There was a problem communicating with Wallet's Wallet API.

        Returns:
            dict: {
                businessId: int, # id of the business who owns the wallet.
                accountNumber: str, # account number of the wallet.
                alias: str, # name of the wallet.
                bankName: str, # name of the bank associated with the wallet.
            }
        """
        return self.wallet_api_client.get_account_for_business_by_account_number(business_id, account_number)

    def get_balance_by_account_number(self, account_number):
        """Retrieves the balance of the given account.

        Args:
            account_number (str): account number.

        Raises:
            WalletNotFoundException: there is no Wallet with the provided account number.
            hee: HttpErrorException as thrown by the "requests" library.
            UnknownTransactionApiException: There was a problem communicating with Wallet's Transaction API.

        Returns:
            dict:
            {
                accountNumber: str, # account number.
                balance: float | int, # balance of the account.
            }
        """
        return self.transaction_api_client.get_balance_by_account_number(account_number)

    def get_balance_by_business_id(self, business_id):
        """Retrieves the balance of the first wallet owned by the business id provided.
        Support for multiple wallets will be supported very soon.

        Args:
            business_id (int): account number.

        Raises:
            WalletNotFoundException: there is no Wallet owned by the provided business id.
            hee: HttpErrorException as thrown by the "requests" library.
            UnknownTransactionApiException: There was a problem communicating with Wallet's Transaction API.

        Returns:
            dict:
            {
                accountNumber: str, # account number.
                balance: float | int, # balance of the account.
            }
        """
        accounts = self.get_accounts_by_business_id(business_id)

        return self.transaction_api_client.get_balance_by_account_number(accounts["accounts"][0]["accountNumber"])

    def create_cashout(self, payload):
        """Created a Cash-Out transaction. If the transactions exists, returns the current status.

        Args:
            payload (dict):
            {
                fromAccount: str, # source account
                payOrderRequests: [ # list of pay orders
                    {
                        id: str, # transaction id.
                        toAccount: str, # source account.
                        amount: float | int, # transaction amount.
                        concept: str, # transaction description.
                        beneficiaryName: str, # destination account owner's name.
                        referenceNumber: str, # tracking number.
                        beneficiaryIdentifier: str, # destination account owner's identifier.
                    },
                    ...
                ]
            }

        Raises:
            InvalidBeneficiaryIdentifierException: invalid source account owner's identifier.
            NotEnoughWalletBalanceException: not enough balance to process the transaction.
            WalletNotFoundException: the account does not exist.
            hee: HttpErrorException as thrown by the "requests" library.
            UnknownTransactionApiException: There was a problem communicating with Wallet's Transaction API.

        Returns:
            list: [ # list of executed pay orders
                {
                    id: str, # transaction id.
                    fromAccount: str, # source account.
                    toAccount: str, # destination account.
                    amount: float | int, # transaction amount.
                    status: str, # status of the transaction.
                    createdAt: str, # creation date and time.
                },
                ...
            ]

            Possible values for status are:
             - INITIATED: the transaction is waiting to be processed.
             - IN_PROGRESS: the transaction is in progress.
             - DEBITED: the transaction was successfully processed.
             - FAILED: the transaction failed. There are many reasons for this, e.g. insufficient balance.
              -ERROR = there was an error processing the transaction, e.g. the provider is down.
        """
        return self.transaction_api_client.create_cashout(payload)

    def check_account_verification_status(self, payload):
        """Obtains the verification status of a given account.

        Args:
            payload (dict) -- the expected payload is as follows:
            {
                accounts: [ # list of accounts to check status.
                    {
                        accountNumber: str, # account number to check.
                        identifier: str, # identifier of the supposed owner of the account, e.g. RFC.
                        name: str, # name of the supposed owner of the account.
                    },
                    ...
                ]
            }

        Raises:
            UnknownAccountApiException: There was a problem communicating with Wallet's Account API.

        Returns:
            dict: {
                accounts: [ # list of checked accounts.
                    {
                        accountNumber: str, # provided account number.
                        identifier: str, # provided id.
                        name: str, # real name of the owner.
                        status: str, # status of the account.
                    },
                    ...
                ]
            }

            Possible values for status are:
            - UNVERIFIED: The account is in the verification queue waiting to be verified.
            - VERIFYING: The account left the que and the verification process is ongoing.
            - VERIFIED: The verification is completed and the account and id provided match.
            - INVALID: The verification is completed and the account and id provided don't match.
            - FAILED: The verification failed. This can happen for a number of reasons, e.g. the account
                      no longer exists.
        """
        return self.account_api_client.check_verification_status(payload)

    def get_cep_info_from_transaction_info(self, params):
        """Obtains the name and rfc from official transfer receipt (CEP) related to a verification check.
        This is specific to Mexico.

        Args:
            params (dict): Data required for obtaining a CEP. The expected parameters are:
             - date (str): Date of the transfer. The expected format is 'DD-MM-YYYY'.
             - reference (str): reference for finding the transfer receipt. Format varies depending on the destination bank.
             - sourceBank (str): code of the bank sending the transfer. The format is '[0-9]{3}'.
             - destinationBank (str): code of the bank receiving the transfer. Same format as sourceBank.
             - destinationAccountNumber (str): account receiving the transfer. Format varies.
             - amount (str | float): transfer amount with two decimal places.

        Raises:
            CepTransactionWasRefundedException: No CEP is available because the verification transaction was refunded
            CepNotFoundException: The CEP could not be retrieved.
            UnknownAccountApiException: There was a problem communicating with Wallet's Account API.

        Returns: dictionary with the following structure
            dict: {
                name: str, # name as appears in the CEP
                rfc: RFC as appears in the CEP
            }
        """
        return self.account_api_client.get_cep_info_from_transaction_info(params)

    def get_account_verified_by_transactions(self, params):
        """Obtains a list of operations for a given date window.
        Yes, the name is misleading, it will be fixed at some point.

        Args:
            params (dict): expected query params:
             - from (str): starting date (inclusive), in 'YYYYMMDD' format.
             - to (str): end date (inclusive), in 'YYYYMMDD' format.
             - page (str | int): page number.
             - limit (str | int): number of transactions per page.

        Raises:
            UnknownBbvaApiErrorException: There was a problem communicating with Wallet's BBVA API.

        Returns:
            list: {
                date: str, # movement date.
                description: str, # operation description.
                cashOutAmount: number, # cash out amount, in the case the operation is outbound.
                cashInAmount: number, # cash in amount, in the case the operation is inbound.
                balance: number, # account balance after the operation.
                rfc: str, # account owner's RFC.
                accountClabe: str, # account number associated with the operation.
                accountName: str, # name of the owner of the account.
                reference: str, # operation reference str.

            } 
        """
        return self.bbva_api_client.get_account_verified_by_transactions(params)
