
"""Transaction Api Client Tests."""
import pytest

from unittest.mock import Mock

from ...exceptions.request.http_error_exception import HttpErrorException
from ...exceptions.transaction.invalid_beneficiary_identifier_exception import InvalidBeneficiaryIdentifierException
from ...exceptions.transaction.not_enough_wallet_balance_exception import NotEnoughWalletBalanceException
from ...exceptions.transaction.unknown_transaction_api_exception import UnknownTransactionApiException
from ...exceptions.transaction.wallet_not_found_exception import WalletNotFoundException

from .transaction_api_client import TransactionApiClient


def describe_transaction_api_client():

    # The actual value doesn't really matter because the client just echoes whatever Wallet sends.
    # All we need to do is check the value we get at the end matches the one returned by secure_request().
    return_value = "return value"

    @pytest.fixture
    def client():
        """Generates a client with encryption disabled, as it was already tested in the parent class, SecureApiClient."""

        client = TransactionApiClient("", use_encryption=False)

        client.secure_request = Mock(return_value=return_value)

        yield client

    def check_prefix(client):
        """Tests if the client is created with the correct prefix."""

        assert client.prefix == "transactions"

    def describe_get_balance_by_account_number():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.get_balance_by_account_number(
                "account number") == return_value

            client.secure_request.assert_called_with(
                url="balance/account number", method="GET")

        def raises_wallet_not_found_exception(client):
            """Tests an WalletNotFoundException is raised if secure_request raises an HttpErrorException with status 404."""

            client.secure_request.side_effect = HttpErrorException("url", 404)

            with pytest.raises(WalletNotFoundException):
                client.get_balance_by_account_number("account number")

        def raises_unknown_transaction_api_exception_by_default(client):
            """Tests an UnknownTransactionApiException is raised if secure_request raises any kind
            of exception other than HttpErrorException with status 404."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownTransactionApiException):
                client.get_balance_by_account_number("account number")

    def describe_create_cashout():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.create_cashout(
                "payload") == return_value

            client.secure_request.assert_called_with(
                url="cash-out", method="POST", payload="payload")

        def raises_invalid_beneficiary_identifier_exception(client):
            """Tests a InvalidBeneficiaryIdentifierException is raised if secure_request raises an HttpErrorException with status 400."""

            client.secure_request.side_effect = HttpErrorException("url", 400)

            payload = {
                "payOrdersRequest": [{
                    "beneficiaryIdentifier": "identifier"
                }]
            }

            with pytest.raises(InvalidBeneficiaryIdentifierException):
                client.create_cashout(payload)

        def raises_not_enough_wallet_balance_exception(client):
            """Tests a NotEnoughWalletBalanceException is raised if secure_request raises an HttpErrorException with status 402."""

            client.secure_request.side_effect = HttpErrorException("url", 402)

            with pytest.raises(NotEnoughWalletBalanceException):
                client.create_cashout({"fromAccount": "account"})

        def raises__wallet_not_found_exception(client):
            """Tests a WalletNotFoundException is raised if secure_request raises an HttpErrorException with status 404."""

            client.secure_request.side_effect = HttpErrorException("url", 404)

            with pytest.raises(WalletNotFoundException):
                client.create_cashout({"fromAccount": "account"})

        def raises_unknown_transaction_api_exception(client):
            """Tests a UnknownTransactionApiException is raised if secure_request raises an HttpErrorException with status other than 400, 402, or 404."""

            client.secure_request.side_effect = HttpErrorException("url", 401)

            with pytest.raises(UnknownTransactionApiException):
                client.create_cashout({"fromAccount": "account"})

        def raises_unknown_transaction_api_exception_by_default(client):
            """Tests a UnknownTransactionApiException is raised if secure_request raises any exception other than HttpErrorException."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownTransactionApiException):
                client.create_cashout("payload")
