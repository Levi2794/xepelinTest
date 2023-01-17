"""BBVA API Client."""

from ...exceptions.bbva.unknown_bbva_api_exception import UnknownBbvaApiException

from ..secure_api_client import SecureApiClient


class BbvaApiClient(SecureApiClient):
    """Client for connecting to Wallet's BBVA API."""

    def __init__(self, base_url, private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """BbvaApiClient constructor

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.
        """
        super().__init__(base_url, "bbva", private_key,
                         passphrase, public_key, use_encryption)

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
        try:
            return self.secure_request(url="transactions", method="GET", params=params)
        except Exception as e:
            raise UnknownBbvaApiException(e)
