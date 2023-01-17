""" Wallet Client Tests."""

import pytest

from unittest.mock import Mock

from .clients.account.account_api_client import AccountApiClient
from .clients.bbva.bbva_api_client import BbvaApiClient
from .clients.transaction.transaction_api_client import TransactionApiClient
from .clients.wallet.wallet_api_client import WalletApiClient

from .wallet_client import WalletClient


def describe_wallet_client():

    return_value = "return value"

    mock = Mock(return_value=return_value)

    @pytest.fixture
    def account_api_client():
        """Generates an account api client."""

        client = AccountApiClient("", use_encryption=False)

        client.check_verification_status = mock
        client.get_cep_info_from_transaction_info = mock

        yield client

    @pytest.fixture
    def bbva_api_client():
        """Generates a bbva api client."""

        client = BbvaApiClient("", use_encryption=False)

        client.get_account_verified_by_transactions = mock

        yield client

    @pytest.fixture
    def transaction_api_client():
        """Generates a transaction api client."""

        client = TransactionApiClient("", use_encryption=False)

        client.get_balance_by_account_number = mock
        client.create_cashout = mock

        yield client

    @pytest.fixture
    def wallet_api_client():
        """Generates a wallet api client."""

        client = WalletApiClient("", use_encryption=False)

        client.create_wallet = mock
        client.get_accounts_by_business_id = mock
        client.get_account_for_business_by_account_number = mock

        yield client

    @pytest.fixture
    def client(account_api_client, bbva_api_client, transaction_api_client, wallet_api_client):
        """Generates a wallet client."""

        client = WalletClient("url", use_encryption=False)

        client.account_api_client = account_api_client
        client.bbva_api_client = bbva_api_client
        client.transaction_api_client = transaction_api_client
        client.wallet_api_client = wallet_api_client

        yield client

    # Accounts
    def check_verification_status(client):
        """Tests account verification."""

        assert client.check_account_verification_status(
            "payload") == return_value

    def get_cep_info_from_transaction_info(client):
        """Tests get CEP."""

        assert client.get_cep_info_from_transaction_info(
            "params") == return_value

    # BBVA
    def get_account_verified_by_transactions(client):
        """Tests get account verified by transaction."""

        assert client.get_account_verified_by_transactions(
            "params") == return_value

    # Transactions
    def get_balance_by_account_number(client):
        """Tests get balance by account number."""

        assert client.get_balance_by_account_number(
            "account_number") == return_value

    def create_cashout(client):
        """Tests create cashout."""

        assert client.create_cashout(
            "params") == return_value

    # Wallets
    def create_wallet(client):
        """Tests wallet creation."""

        assert client.create_wallet("payload") == return_value

    def get_accounts_by_business_id(client):
        """Tests get account by business id."""

        assert client.get_accounts_by_business_id(
            "account_number") == return_value

    def get_account_for_business_by_account_number(client):
        """Tests get account for business by account number."""

        assert client.get_account_for_business_by_account_number(
            1, "account_number") == return_value
