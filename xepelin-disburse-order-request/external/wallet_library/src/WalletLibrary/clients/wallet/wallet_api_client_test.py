"""Wallet Api Client Tests."""

import pytest

from unittest.mock import Mock

from ...exceptions.request.http_error_exception import HttpErrorException
from ...exceptions.wallet.account_not_found_for_business_id_exception import AccountNotFoundForBusinessIdException
from ...exceptions.wallet.invalid_identifier_exception import InvalidIdentifierException
from ...exceptions.wallet.unknown_wallet_api_exception import UnknownWalletApiException


from .wallet_api_client import WalletApiClient


def describe_wallet_api_client():

    # The actual value doesn't really matter because the client just echoes whatever Wallet sends.
    # All we need to do is check the value we get at the end matches the one returned by secure_request().
    return_value = "return value"

    @pytest.fixture
    def client():
        """Generates a client with encryption disabled, as it was already tested in the parent class, SecureApiClient."""

        client = WalletApiClient("", use_encryption=False)

        client.secure_request = Mock(return_value=return_value)

        yield client

    def check_prefix(client):
        """Tests if the client is created with the correct prefix."""

        assert client.prefix == "wallets"

    def describe_create_wallet():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.create_wallet("payload") == return_value

            client.secure_request.assert_called_with(
                url="", method="POST", payload="payload")

        def raises_invalid_identifier_exception(client):
            """Tests if an InvalidIdentifierException is raised if secure_request raises an HttpErrorException with status 400."""

            client.secure_request.side_effect = HttpErrorException("url", 400)

            with pytest.raises(InvalidIdentifierException):
                client.create_wallet({"identifier": "identifier"})

        def raises_invalid_identifier_exception(client):
            """Tests if an UnknownWalletApiException is raised if secure_request raises an HttpErrorException with status other than 400."""

            client.secure_request.side_effect = HttpErrorException("url", 401)

            with pytest.raises(UnknownWalletApiException):
                client.create_wallet("payload")

        def raises_invalid_identifier_exception_by_default(client):
            """Tests if an UnknownWalletApiException is raised if secure_request raises an exception other than HttpErrorException."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownWalletApiException):
                client.create_wallet("payload")

    def describe_get_accounts_by_business_id():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.get_accounts_by_business_id(1) == return_value

            client.secure_request.assert_called_with(
                url="accounts/1", method="GET")

        def raises_account_not_found_for_business_id_exception(client):
            """Tests if an AccountNotFoundForBusinessIdException is raised if secure_request raises an HttpErrorException with status 404."""

            client.secure_request.side_effect = HttpErrorException("url", 404)

            with pytest.raises(AccountNotFoundForBusinessIdException):
                client.get_accounts_by_business_id(1)

        def raises_invalid_identifier_exception(client):
            """Tests if an UnknownWalletApiException is raised if secure_request raises an HttpErrorException with status other than 404."""

            client.secure_request.side_effect = HttpErrorException("url", 401)

            with pytest.raises(UnknownWalletApiException):
                client.get_accounts_by_business_id(1)

        def raises_invalid_identifier_exception_by_default(client):
            """Tests if an UnknownWalletApiException is raised if secure_request raises an exception other than HttpErrorException."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownWalletApiException):
                client.get_accounts_by_business_id(1)

    def describe_get_account_for_business_by_account_number():

        def returns_an_account_if_found(client):
            """Tests if an account if returned if found for a given business_id/account_number tuple."""

            account = {
                "accountNumber": "existing_account_number",
            }

            accounts = {
                "accounts": [account]
            }

            client.get_accounts_by_business_id = Mock(return_value=accounts)

            found_account = client.get_account_for_business_by_account_number(
                1, "existing_account_number")

            assert found_account == account

        def raises_account_not_found_for_business_id_exception(client):
            """Tests if an AccountNotFoundForBusinessIdException is raised if no account was found."""

            account = {
                "accountNumber": "existing_account_number",
            }

            accounts = {
                "accounts": [account]
            }

            client.get_accounts_by_business_id = Mock(return_value=accounts)

            with pytest.raises(AccountNotFoundForBusinessIdException):
                client.get_account_for_business_by_account_number(
                    1, "non_existing_account_number")
