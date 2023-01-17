"""Crypto Service Tests."""

import pytest

from unittest.mock import patch

from .crypto_service import CryptoService, EncryptedPayload

from ..exceptions.crypto.load_key_exception import LoadKeyException
from ..exceptions.crypto.unknown_crypto_exception import UnknownCryptoException
from ..exceptions.crypto.encrypt_crypto_data_exception import EncryptCryptoDataException
from ..exceptions.crypto.encrypt_payload_exception import EncryptPayloadException
from ..exceptions.crypto.signature_creation_exception import SignatureCreationException
from ..exceptions.response.decrypt_crypto_data_exception import DecryptCryptoDataException
from ..exceptions.response.decrypt_payload_exception import DecryptPayloadException
from ..exceptions.response.signature_does_not_match_exception import SignatureDoesNotMatchException
from ..exceptions.response.signature_verification_exception import SignatureVerificationException

some_payload = "some payload"
some_encrypted_payload = "some encrypted payload"

some_encrypted_crypto_data = "some encrypted crypto data"
some_decrypted_crypto_data = "key|iv"
some_key = "key"
some_iv = "iv"

some_signature = "some signature"


def create_crypto_service() -> CryptoService:
    """Create a CryptoService instance.

    Returns:
        CryptoService: A CryptoService instance.
    """

    with patch("WalletCrypto.wallet_crypto.load_rsa_key", return_value=""):
        return CryptoService("some private key", "some passphrase", "some public key")


crypto_service = create_crypto_service()


def describe_encrypted_payload():

    def describe_creation():

        def wrong_param_types():
            """Tests if EncryptedPayload constructor raises the correct exception
            when given params of the wrong type."""

            with pytest.raises(TypeError):
                EncryptedPayload(1, "", "")
                EncryptedPayload("", 1, "")
                EncryptedPayload("", "", 1)

    def should_build_a_payload_with_the_correct_format():
        """Tests if the encrypted payload is created correctly."""

        created_payload = EncryptedPayload(
            some_encrypted_payload, some_signature, some_encrypted_crypto_data).create_payload()

        assert created_payload["encrypted_body"]["encryptedPayload"] == some_encrypted_payload
        assert created_payload["signature_header"] == some_signature
        assert created_payload["encryption_header"] == some_encrypted_crypto_data


def describe_crypto_service():

    def describe_crypto_service_creation():

        def wrong_param_types():
            """Tests if CryptoService constructor fails with params of the wrong type."""

            with pytest.raises(TypeError):
                CryptoService(1, "", "")
                CryptoService("", 1, "")
                CryptoService("", "", 1)

        def bad_private_key_or_wrong_passphrase():
            """Should rise a LoadKeyException if the private key is bad in some way or the wrong
            passphrase is provided."""

            with patch("WalletCrypto.wallet_crypto.load_rsa_key", side_effect=ValueError()):
                with pytest.raises(LoadKeyException):
                    CryptoService("some private key",
                                  "some passphrase", "some public key")

        def unknown_load_private_key_exception():
            """Should rise an UnknownCryptoException if the private key loading process raises an
            unknown exception."""

            with patch("WalletCrypto.wallet_crypto.load_rsa_key", side_effect=Exception()):
                with pytest.raises(UnknownCryptoException):
                    CryptoService("some private key",
                                  "some passphrase", "some public key")

        def bad_public_key_or_wrong_passphrase():
            """Should rise a LoadKeyException if the public key is bad in some way or the wrong
            passphrase is provided."""

            with patch("WalletCrypto.wallet_crypto.load_rsa_key", side_effect=["", ValueError()]):
                with pytest.raises(LoadKeyException):
                    CryptoService("some private key",
                                  "some passphrase", "some public key")

        def unknown_load_public_key_exception():
            """Should rise an UnknownCryptoException if the public key loading process raises an
            unknown exception."""

            with patch("WalletCrypto.wallet_crypto.load_rsa_key", side_effect=["", Exception()]):
                with pytest.raises(UnknownCryptoException):
                    CryptoService("some private key",
                                  "some passphrase", "some public key")

    def describe_encrypt():

        def happy_path():
            """Tests encryption happy path."""

            crypto_service = create_crypto_service()

            with patch("WalletCrypto.wallet_crypto.aes_encrypt", return_value=(some_encrypted_payload, some_key, some_iv)):
                with patch("WalletCrypto.wallet_crypto.sign", return_value=some_signature):
                    with patch("WalletCrypto.wallet_crypto.rsa_encrypt", return_value=some_encrypted_crypto_data):
                        encrypted_payload = crypto_service.encrypt_and_sign(
                            "some payload")

                        assert encrypted_payload["encrypted_body"]["encryptedPayload"] == some_encrypted_payload
                        assert encrypted_payload["signature_header"] == some_signature
                        assert encrypted_payload["encryption_header"] == some_encrypted_crypto_data

        def bad_params():
            """Should raise a TypeError if payload is not a string."""

            with pytest.raises(TypeError):
                crypto_service.decrypt_and_verify(1)

        def payload_encryption_fails():
            """Should raise a EncryptPayloadException if the payload encryption fails."""

            with patch("WalletCrypto.wallet_crypto.aes_encrypt", side_effect=Exception()):
                with pytest.raises(EncryptPayloadException):
                    crypto_service.encrypt_and_sign(some_payload)

        def payload_signature_creation_fails():
            """Should raise a SignatureCreationException if the signing process fails."""

            with patch("WalletCrypto.wallet_crypto.aes_encrypt", return_value=(some_encrypted_payload, some_key, some_iv)):
                with patch("WalletCrypto.wallet_crypto.sign", side_effect=Exception()):
                    with pytest.raises(SignatureCreationException):
                        crypto_service.encrypt_and_sign(some_payload)

        def payload_crypto_data_encryption_fails():
            """Should raise a EncryptCryptoDataException if the crypto data encryption fails."""

            with patch("WalletCrypto.wallet_crypto.aes_encrypt", return_value=(some_encrypted_payload, some_key, some_iv)):
                with patch("WalletCrypto.wallet_crypto.sign", return_value=some_signature):
                    with patch("WalletCrypto.wallet_crypto.rsa_encrypt", side_effect=Exception()):
                        with pytest.raises(EncryptCryptoDataException):
                            crypto_service.encrypt_and_sign(some_payload)

    def describe_decrypt():

        def happy_path():
            """Tests decryption happy path."""

            with patch("WalletCrypto.wallet_crypto.rsa_decrypt", return_value=some_decrypted_crypto_data):
                with patch("WalletCrypto.wallet_crypto.verify_signature"):
                    with patch("WalletCrypto.wallet_crypto.aes_decrypt", return_value=some_payload):
                        decrypted_payload = crypto_service.decrypt_and_verify(
                            some_encrypted_payload, some_signature, some_encrypted_crypto_data)

                        assert decrypted_payload == some_payload

        def bad_params():
            """Should raise a TypeError if any of the params is not a string."""

            with pytest.raises(TypeError):
                crypto_service.decrypt_and_verify(1, "", "")
                crypto_service.decrypt_and_verify("", 1, "")
                crypto_service.decrypt_and_verify("", "", 1)

        def bad_crypto_data():
            """Should raise a DecryptCryptoDataException if decrypting the crypto data fails."""

            with patch("WalletCrypto.wallet_crypto.rsa_decrypt", side_effect=Exception()):
                with pytest.raises(DecryptCryptoDataException) as e:
                    crypto_service.decrypt_and_verify(
                        some_encrypted_payload, some_signature, some_encrypted_crypto_data)

        def bad_signature():
            """Should raise a SignatureVerificationException if the signature does not match."""

            with patch("WalletCrypto.wallet_crypto.rsa_decrypt", return_value=some_decrypted_crypto_data):
                with patch("WalletCrypto.wallet_crypto.verify_signature", side_effect=ValueError()):
                    with pytest.raises(SignatureDoesNotMatchException) as e:
                        crypto_service.decrypt_and_verify(
                            some_encrypted_payload, some_signature, some_encrypted_crypto_data)

        def sign_verification_failed():
            """Should raise a SignatureVerificationException if the signature verification fails."""

            with patch("WalletCrypto.wallet_crypto.rsa_decrypt", return_value=some_decrypted_crypto_data):
                with patch("WalletCrypto.wallet_crypto.verify_signature", side_effect=Exception()):
                    with pytest.raises(SignatureVerificationException) as e:
                        crypto_service.decrypt_and_verify(
                            some_encrypted_payload, some_signature, some_encrypted_crypto_data)

        def bad_payload():
            """Should raise a DecryptPayloadException if decrypting the payload fails."""

            with patch("WalletCrypto.wallet_crypto.rsa_decrypt", return_value=some_decrypted_crypto_data):
                with patch("WalletCrypto.wallet_crypto.verify_signature"):
                    with patch("WalletCrypto.wallet_crypto.aes_decrypt", side_effect=ValueError()):
                        with pytest.raises(DecryptPayloadException):
                            crypto_service.decrypt_and_verify(
                                some_encrypted_payload, some_signature, some_encrypted_crypto_data)
