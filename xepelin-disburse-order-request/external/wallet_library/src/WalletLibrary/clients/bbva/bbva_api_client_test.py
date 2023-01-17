
"""BBVA Api Client Tests."""
import pytest

from unittest.mock import Mock

from ...exceptions.bbva.unknown_bbva_api_exception import UnknownBbvaApiException

from .bbva_api_client import BbvaApiClient


def describe_bbva_api_client():

    # The actual value doesn't really matter because the client just echoes whatever Wallet sends.
    # All we need to do is check the value we get at the end matches the one returned by secure_request().
    return_value = "return value"

    @pytest.fixture
    def client():
        """Generates a client with encryption disabled, as it was already tested in the parent class, SecureApiClient."""

        client = BbvaApiClient("", use_encryption=False)

        client.secure_request = Mock(return_value=return_value)

        yield client

    def check_prefix(client):
        """Tests if the client is created with the correct prefix."""

        assert client.prefix == "bbva"

    def describe_get_account_verified_by_transactions():

        def happy_path(client):
            """Tests if the client makes the correct request and echoes Wallet's response."""

            assert client.get_account_verified_by_transactions(
                "params") == return_value

            client.secure_request.assert_called_with(
                url="transactions", method="GET", params="params")

        def secure_request_raises_unknown_bbva_api_exception_by_default(client):
            """Tests an UnknownBbvaApiException is raised if secure_request raises an exception of any kind."""

            client.secure_request.side_effect = Exception()

            with pytest.raises(UnknownBbvaApiException):
                client.get_account_verified_by_transactions("params")
