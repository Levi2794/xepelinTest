
"""Account Api Client Tests."""
import pytest

from unittest.mock import Mock

from ...exceptions.account.cep_not_found_exception import CepNotFoundException
from ...exceptions.account.cep_transaction_was_refunded_exception import CepTransactionWasRefundedException
from ...exceptions.account.unknown_account_api_exception import UnknownAccountApiException
from ...exceptions.request.http_error_exception import HttpErrorException

from .account_api_client import AccountApiClient


def describe_account_api_client():

    # The actual value doesn't really matter because the client just echoes whatever Wallet sends.
    # All we need to do is check the value we get at the end matches the one returned by secure_request().
    return_value = "return value"

    @pytest.fixture
    def client():
        """Generates a client with encryption disabled, as it was already tested in the parent class, SecureApiClient."""

        client = AccountApiClient("", use_encryption=False)

        client.secure_request = Mock(return_value=return_value)

        yield client

    def check_prefix(client):
        """Tests if the client is created with the correct prefix."""

        assert client.prefix == "accounts"

    def describe_check_verification_status():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.check_verification_status("payload") == return_value

            client.secure_request.assert_called_with(
                url="check", method="POST", payload="payload")

        def raises_unknown_account_api_exception(client):
            """Tests if an UnknownAccountApiException is raised if secure_request raises an exception of any kind."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownAccountApiException):
                client.check_verification_status("payload")

    def describe_get_cep_info_from_transaction_info():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.get_cep_info_from_transaction_info(
                "params") == return_value

            client.secure_request.assert_called_with(
                url="cep", method="GET", params="params")

        def raises_cep_transaction_wa_refunded_exception(client):
            """Tests a CepTransactionWasRefundedException is raised if secure_request raises an HttpErrorException with status 400."""

            client.secure_request.side_effect = HttpErrorException("url", 400)

            with pytest.raises(CepTransactionWasRefundedException):
                client.get_cep_info_from_transaction_info("params")

        def raises_cep_not_found_exception(client):
            """Tests a CepNotFoundException is raised if secure_request raises an HttpErrorException with status 404."""

            client.secure_request.side_effect = HttpErrorException("url", 404)

            with pytest.raises(CepNotFoundException):
                client.get_cep_info_from_transaction_info("params")

        def raises_unknown_account_api_exception(client):
            """Tests a CepNotFoundException is raised if secure_request raises an HttpErrorException with status other than 400 or 404."""

            client.secure_request.side_effect = HttpErrorException("url", 401)

            with pytest.raises(UnknownAccountApiException):
                client.get_cep_info_from_transaction_info("params")

        def raises_unknown_account_api_exception_by_default(client):
            """Tests a CepNotFoundException is raised if secure_request raises any exception other than HttpErrorException."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownAccountApiException):
                client.get_cep_info_from_transaction_info("params")
