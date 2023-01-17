"""Wallet API Client."""

from ...exceptions.request.http_error_exception import HttpErrorException
from ...exceptions.wallet.account_not_found_for_business_id_exception import AccountNotFoundForBusinessIdException
from ...exceptions.wallet.invalid_identifier_exception import InvalidIdentifierException
from ...exceptions.wallet.unknown_wallet_api_exception import UnknownWalletApiException

from ..secure_api_client import SecureApiClient


class WalletApiClient(SecureApiClient):
    """Client for connecting to Wallet's Wallet API."""

    def __init__(self, base_url, private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """WalletApiClient constructor

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.
        """
        super().__init__(base_url, "wallets", private_key,
                         passphrase, public_key, use_encryption)

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
            InvalidIdentifierException: owner identifier is not valid.
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
        try:
            return self.secure_request(url="", method="POST", payload=payload)
        except HttpErrorException as hee:
            if hee.status == 400:
                raise InvalidIdentifierException(payload["identifier"])

            raise UnknownWalletApiException(hee)
        except Exception as e:
            raise UnknownWalletApiException(e)

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
        try:
            return self.secure_request(url=f"accounts/{business_id}", method="GET")
        except HttpErrorException as hee:
            if hee.status == 404:
                raise AccountNotFoundForBusinessIdException(business_id)

            raise UnknownWalletApiException(hee)
        except Exception as e:
            raise UnknownWalletApiException(e)

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
        business_accounts = self.get_accounts_by_business_id(business_id)

        found_account = None

        for account in business_accounts["accounts"]:
            if account["accountNumber"] == account_number:
                found_account = account

                break

        if found_account:
            return found_account

        raise AccountNotFoundForBusinessIdException(business_id)
