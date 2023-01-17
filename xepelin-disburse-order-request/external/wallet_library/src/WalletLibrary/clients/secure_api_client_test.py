"""Secure Api Client Tests."""

import pytest
import json

from unittest.mock import MagicMock, patch

from .secure_api_client import SecureApiClient

from ..constants.crypto import EMPTY_BODY_STRING, ENCRYPTION_HEADER, SIGNATURE_HEADER

from ..services.crypto_service import CryptoService, EncryptedPayload

from ..exceptions.crypto.missing_key_exception import MissingKeyException
from ..exceptions.crypto.missing_private_key_passphrase_exception import MissingPrivateKeyPassphraseException
from ..exceptions.request.http_error_exception import HttpErrorException
from ..exceptions.response.bad_json_received_exception import BadJsonReceivedException
from ..exceptions.response.crypto_header_missing_exception import CryptoHeaderMissingException
from ..exceptions.response.malformed_body_exception import MalformedBodyException
from ..exceptions.response.signature_header_missing_exception import SignatureHeaderMissingException
from ..exceptions.response.unexpected_empty_body_received_exception import UnexpectedEmptyBodyReceivedException
from ..exceptions.unknown_api_exception import UnknownApiException


def describe_secure_api_client():

    def describe_creation():

        def bad_params():
            """Tests if SecureApiClient constructor raises the correct exception
            when given params of the wrong type."""

            with pytest.raises(TypeError):
                SecureApiClient(1, "", "", "", "", True)

            with pytest.raises(TypeError):
                SecureApiClient("", 1, "", "", "", True)

            with pytest.raises(TypeError):
                SecureApiClient("", "", 1, "", "", True)

            with pytest.raises(TypeError):
                SecureApiClient("", "", "", 1, "", True)

            with pytest.raises(TypeError):
                SecureApiClient("", "", "", "", 1, True)

            with pytest.raises(TypeError):
                SecureApiClient("", "", "", "", "", "")

        def missing_keys_or_passphrase_when_encryption_is_enabled():
            """Tests if SecureApiClient constructor raises the correct exception
            when a private, public, and passphrase are expected because encryption is enabled."""

            with pytest.raises(MissingKeyException):
                SecureApiClient("")
                SecureApiClient("", private_key="key", passphrase="key")

            with pytest.raises(MissingPrivateKeyPassphraseException):
                SecureApiClient("", private_key="key")

    def describe_build_url():

        def build_the_correct_url_prefix_and_path():
            """Should build the correct url of both prefix and path are not empty."""

            sac = SecureApiClient("", "prefix", use_encryption=False)

            assert sac.build_url("path") == "prefix/path"

        def build_the_correct_url_just_prefix():
            """Should build the correct url of just prefix is not empty."""

            sac = SecureApiClient("", "prefix", use_encryption=False)

            assert sac.build_url() == "prefix"

        def build_the_correct_url_just_path():
            """Should build the correct url of just path is not empty."""

            sac = SecureApiClient("", "", use_encryption=False)

            assert sac.build_url("path") == "path"

    def describe_secure_request():

        mock_response = MagicMock()

        mock_encrypted_and_signed_payload = {
            "encrypted_body": "some encrypted payload",
            "signature_header": "some signature header",
            "encryption_header": "some encryption header",
        }

        @pytest.fixture(autouse=True)
        def init_mock_response():
            mock_response.status_code = 200

            mock_response.json.return_value = {
                "encryptedPayload": "some encrypted payload",
                "signature_header": "some signature header",
                "encryption_header": "some encryption header",
            }
            mock_response.headers = {
                SIGNATURE_HEADER: "some signature header",
                ENCRYPTION_HEADER: "some encryption header",
            }

        def describe_happy_path():

            def encryption_disabled():
                """Should complete a request when encryption is disabled."""

                sac = SecureApiClient("base_url", use_encryption=False)

                mock_response.text = "text"

                with patch("requests.request", return_value=mock_response):
                    response = sac.secure_request("url", "get")

                    assert response == "text"

            def encryption_enabled():
                """Should complete a request when encryption is enabled."""

                response_body = {
                    "some_field": "some value"
                }

                with patch.object(CryptoService, "__init__", return_value=None):
                    with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                        with patch.object(CryptoService, "decrypt_and_verify", return_value=json.dumps(response_body)):
                            with patch("requests.request", return_value=mock_response):
                                sac = SecureApiClient("base_url", private_key="private key",
                                                      passphrase="passphrase", public_key="public key", use_encryption=True)

                                response = sac.secure_request(
                                    "url", "get", empty_body_expected=True)

                                assert response == response_body

                def encryption_enabled_empty_body():
                    """Should complete a request when encryption is enabled and the response body is empty."""

                    with patch.object(CryptoService, "__init__", return_value=None):
                        with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                            with patch.object(CryptoService, "decrypt_and_verify", return_value=EMPTY_BODY_STRING):
                                with patch("requests.request", return_value=mock_response):
                                    sac = SecureApiClient("base_url", private_key="private key",
                                                          passphrase="passphrase", public_key="public key", use_encryption=True)

                                    response = sac.secure_request(
                                        "url", "get", empty_body_expected=True)

                                    assert response == ""

        def should_fail_if_requests_raises_an_exception():
            """Tests if the client raises an UnknownApiException if requests raises an exception."""

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch("requests.request", side_effect=Exception()):
                        sac = SecureApiClient("base_url", private_key="private key",
                                              passphrase="passphrase", public_key="public key", use_encryption=True)

                        with pytest.raises(UnknownApiException):
                            sac.secure_request("url", "get")

        def should_fail_if_response_status_is_399_or_greater():
            """Tests if the client raises an HttpErrorException if the response status code is >= 400."""

            mock_response.status_code = 400

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch("requests.request", return_value=mock_response):
                        sac = SecureApiClient("base_url", private_key="private key",
                                              passphrase="passphrase", public_key="public key", use_encryption=True)

                        with pytest.raises(HttpErrorException):
                            sac.secure_request("url", "get")

        def should_fail_if_response_body_is_not_json():
            """Tests if the client raises a BadJsonReceivedException if the response body is not valid JSON."""

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch.object(CryptoService, "decrypt_and_verify", return_value="not JSON"):
                        with patch("requests.request", return_value=mock_response):
                            sac = SecureApiClient("base_url", private_key="private key",
                                                  passphrase="passphrase", public_key="public key", use_encryption=True)

                            with pytest.raises(BadJsonReceivedException):
                                sac.secure_request("url", "get")

        def should_fail_if_response_body_does_not_have_the_expected_format():
            """Tests if the client raises a MalformedBodyException if the response body has the wrong format."""

            mock_response.json.return_value = {"bad": "format"}

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch("requests.request", return_value=mock_response):
                        sac = SecureApiClient("base_url", private_key="private key",
                                              passphrase="passphrase", public_key="public key", use_encryption=True)

                        with pytest.raises(MalformedBodyException):
                            sac.secure_request("url", "get")

        def should_fail_if_response_does_not_have_the_signature_header():
            """Tests if the client raises a SignatureHeaderMissingException if the response is missing the signature header."""

            mock_response.headers = {
                ENCRYPTION_HEADER: "some encryption header"
            }

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch("requests.request", return_value=mock_response):
                        sac = SecureApiClient("base_url", private_key="private key",
                                              passphrase="passphrase", public_key="public key", use_encryption=True)

                        with pytest.raises(SignatureHeaderMissingException):
                            sac.secure_request("url", "get")

        def should_fail_if_response_does_not_have_the_encryption_header():
            """Tests if the client raises a CryptoHeaderMissingException if the response is missing the encryption header."""

            mock_response.headers = {
                SIGNATURE_HEADER: "some signature header",
            }

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch("requests.request", return_value=mock_response):
                        sac = SecureApiClient("base_url", private_key="private key",
                                              passphrase="passphrase", public_key="public key", use_encryption=True)

                        with pytest.raises(CryptoHeaderMissingException):
                            sac.secure_request("url", "get")

        def should_fail_if_the_decrypted_payload_is_empty():
            """Tests if the client raises a UnexpectedEmptyBodyReceivedException if the decrypted payload is empty."""

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch.object(CryptoService, "decrypt_and_verify", return_value=""):
                        with patch("requests.request", return_value=mock_response):
                            sac = SecureApiClient("base_url", private_key="private key",
                                                  passphrase="passphrase", public_key="public key", use_encryption=True)

                            with pytest.raises(UnexpectedEmptyBodyReceivedException):
                                sac.secure_request("url", "get")

        def should_fail_if_the_decrypted_payload_is_an_unexpected_empty_body_string():
            """Tests if the client raises a UnexpectedEmptyBodyReceivedException if the payload is EMPTY_BODY_STRING
            but an empty body was not expected."""

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch.object(CryptoService, "decrypt_and_verify", return_value=EMPTY_BODY_STRING):
                        with patch("requests.request", return_value=mock_response):
                            sac = SecureApiClient("base_url", private_key="private key",
                                                  passphrase="passphrase", public_key="public key", use_encryption=True)

                            with pytest.raises(UnexpectedEmptyBodyReceivedException):
                                sac.secure_request("url", "get")

        def should_fail_if_the_decrypted_payload_is_invalid_json():
            """Tests if the client raises a BadJsonReceivedException if the payload is invalid JSON."""

            with patch.object(CryptoService, "__init__", return_value=None):
                with patch.object(CryptoService, "encrypt_and_sign", return_value=mock_encrypted_and_signed_payload):
                    with patch.object(CryptoService, "decrypt_and_verify", return_value="not JSON"):
                        with patch("requests.request", return_value=mock_response):
                            sac = SecureApiClient("base_url", private_key="private key",
                                                  passphrase="passphrase", public_key="public key", use_encryption=True)

                            with pytest.raises(BadJsonReceivedException):
                                sac.secure_request("url", "get")
