"""Account API Client."""

from ...exceptions.account.cep_not_found_exception import CepNotFoundException
from ...exceptions.account.cep_transaction_was_refunded_exception import CepTransactionWasRefundedException
from ...exceptions.account.unknown_account_api_exception import UnknownAccountApiException
from ...exceptions.request.http_error_exception import HttpErrorException

from ..secure_api_client import SecureApiClient


class AccountApiClient(SecureApiClient):
    """Client for connecting to Wallet's Account API."""

    def __init__(self, base_url, private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """AccountApiClient constructor

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.
        """
        super().__init__(base_url, "accounts", private_key,
                         passphrase, public_key, use_encryption)

    def check_verification_status(self, payload):
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
        try:
            return self.secure_request(url="check", method="POST", payload=payload)
        except Exception as e:
            raise UnknownAccountApiException(e)

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
        try:
            return self.secure_request(url="cep", method="GET", params=params)
        except HttpErrorException as hee:
            status = hee.status

            if status == 400:
                raise CepTransactionWasRefundedException(params)

            if status == 404:
                raise CepNotFoundException(params)

            raise UnknownAccountApiException(hee)
        except Exception as e:
            raise UnknownAccountApiException(e)
