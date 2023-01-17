"""Transaction API Client."""

from ...exceptions.request.http_error_exception import HttpErrorException
from ...exceptions.transaction.invalid_beneficiary_identifier_exception import InvalidBeneficiaryIdentifierException
from ...exceptions.transaction.not_enough_wallet_balance_exception import NotEnoughWalletBalanceException
from ...exceptions.transaction.unknown_transaction_api_exception import UnknownTransactionApiException
from ...exceptions.transaction.wallet_not_found_exception import WalletNotFoundException

from ..secure_api_client import SecureApiClient


class TransactionApiClient(SecureApiClient):
    """Client for connecting to Wallet's Transaction API."""

    def __init__(self, base_url, private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """TransactionApiClient constructor

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.
        """
        super().__init__(base_url, "transactions", private_key,
                         passphrase, public_key, use_encryption)

    def get_balance_by_account_number(self, account_number):
        """Retrieves the balance of the given account.

        Args:
            account_number (str): account number.

        Raises:
            WalletNotFoundException: there is no Wallet with the provided account number.
            HttpErrorException: Wrapper for "requests" library exceptions.
            UnknownTransactionApiException: There was a problem communicating with Wallet's Transaction API.

        Returns:
            dict:
            {
                accountNumber: str, # account number.
                balance: float | int, # account balance.
            }
        """
        try:
            return self.secure_request(url=f"balance/{account_number}", method="GET")
        except HttpErrorException as hee:
            if hee.status == 404:
                raise WalletNotFoundException(account_number)

            raise hee
        except Exception as e:
            raise UnknownTransactionApiException(e)

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
        try:
            response = self.secure_request(
                url="cash-out", method="POST", payload=payload)

            return response
        except HttpErrorException as hee:
            status = hee.status

            if status == 400:
                raise InvalidBeneficiaryIdentifierException(
                    payload["payOrdersRequest"][0]["beneficiaryIdentifier"])

            if status == 402:
                raise NotEnoughWalletBalanceException(payload["fromAccount"])

            if status == 404:
                raise WalletNotFoundException(payload["fromAccount"])

            raise UnknownTransactionApiException(hee)
        except Exception as e:
            raise UnknownTransactionApiException(e)
