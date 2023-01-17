from .....wallet_crypto import wallet_crypto as wc

from ..exceptions.crypto.load_key_exception import LoadKeyException
from ..exceptions.crypto.unknown_crypto_exception import UnknownCryptoException
from ..exceptions.crypto.encrypt_crypto_data_exception import EncryptCryptoDataException
from ..exceptions.crypto.encrypt_payload_exception import EncryptPayloadException
from ..exceptions.crypto.signature_creation_exception import SignatureCreationException
from ..exceptions.response.decrypt_crypto_data_exception import DecryptCryptoDataException
from ..exceptions.response.decrypt_payload_exception import DecryptPayloadException
from ..exceptions.response.signature_does_not_match_exception import SignatureDoesNotMatchException
from ..exceptions.response.signature_verification_exception import SignatureVerificationException


class EncryptedPayload:
    """Builder class for an encrypted payload."""

    def __init__(self, encrypted_payload, signature, encrypted_crypto_data):
        """EncryptedPayload constructor.

        Raises:
            TypeError: If any of the params is not a string.

        Args:
            encrypted_payload (str): The encrypted body, base64 encoded.
            signature (str): The cryptographic signature, base64 encoded.
            encrypted_crypto_data (str): The encrypted AES key and iv, base64 encoded.
        """

        if type(encrypted_payload) is not str:
            raise TypeError("encrypted_payload must be a string.")

        if type(signature) is not str:
            raise TypeError("signature must be a string.")

        if type(encrypted_crypto_data) is not str:
            raise TypeError("encrypted_crypto_data must be a string.")

        self.encrypted_payload = encrypted_payload
        self.signature = signature
        self.encrypted_crypto_data = encrypted_crypto_data

    def create_payload(self):
        """Builds an encrypted request.

        Returns:
            dict: The encrypted request.
        """
        return {
            "encrypted_body": {
                "encryptedPayload": self.encrypted_payload
            },
            "signature_header": self.signature,
            "encryption_header": self.encrypted_crypto_data
        }


class CryptoService:
    """Class that handles encryption, decryption, and signature generation and verification.
    It uses Wallet Crypto Library."""

    def __init__(self, private_key, passphrase, public_key):
        """CryptoService constructor

        Args:
            private_key (str): Private key for decryption and signature generation in PEM format.
            passphrase (str): Passphrase for the private key.
            public_key (str): public key for encryption and signature verification in PEM format.

        Raises:
            TypeError: If any of the params is not a string.
            LoadKeyException: RSA key could not be created, probably it has the wrong format or passphrase.
            UnknownCryptoException: Unidentified exception related to the cryptographic process.
        """

        if type(private_key) is not str:
            raise TypeError("private_key must be a string.")

        if type(passphrase) is not str:
            raise TypeError("passphrase must be a string.")

        if type(public_key) is not str:
            raise TypeError("public_key must be a string.")

        try:
            self.private_key = wc.load_rsa_key(private_key, passphrase)
        except ValueError as ve:
            raise LoadKeyException(
                "private", ve)
        except Exception as e:
            raise UnknownCryptoException(e)

        try:
            self.public_key = wc.load_rsa_key(public_key)
        except ValueError as ve:
            raise LoadKeyException("public", ve)
        except Exception as e:
            raise UnknownCryptoException(e)

    def encrypt_and_sign(self, payload):
        """Encrypts a payload using AES256, encrypts AES key and iv using a public key, and finally signs the payload using a private key.

        Args:
            payload (str): The payload to be encrypted. JSON is preferred but not required, any string will do.

        Raises:
            TypeError: payload is not a string.
            EncryptPayloadException: An exception was risen while encrypting the payload.
            SignatureCreationException: The signature could not be created.
            EncryptCryptoDataException: The encryption key and iv could no be encrypted using the public key.

        Returns:
            EncryptedPayload: The encrypted payload, plus crypto and signature headers.
        """

        if type(payload) is not str:
            raise TypeError("payload must be a string")

        # encrypt payload
        try:
            encrypted_payload, key, iv = wc.aes_encrypt(payload)
        except Exception as e:
            raise EncryptPayloadException(e)

        # encode crypto data
        encoded_crypto_data = f"{key}|{iv}"

        # sign
        try:
            signature = wc.sign(self.private_key, encoded_crypto_data)
        except Exception as e:
            raise SignatureCreationException(e)

        # encrypt crypto data
        try:
            encrypted_crypto_data = wc.rsa_encrypt(
                self.public_key, encoded_crypto_data)
        except Exception as e:
            raise EncryptCryptoDataException(e)

        # return encrypted payload
        return EncryptedPayload(encrypted_payload, signature, encrypted_crypto_data).create_payload()

    def decrypt_and_verify(self, encrypted_payload, signature, encrypted_crypto_data):
        """Decrypts AES key and iv using a private key, verifies the signature using a public key,
        and finally decrypts the payload using the key and iv received.

        Args:
            encrypted_payload (str): Encrypted, base64 encoded payload
            signature (str): Cryptographic signature, base64 encoded
            encrypted_crypto_data (str): Encrypted key and iv, base64 encoded.

        Raises:
            TypeError: If encrypted_payload, signature, and/or encrypted_crypto_data are not strings.
            DecryptCryptoDataException: Key and iv could not be decrypted.
            SignatureVerificationException: The signature verification could not be performed.
            SignatureDoesNotMatchException: The signature verification failed.
            DecryptPayloadException: The payload could not be decrypted.

        Returns:
            str: the decrypted payload.
        """

        if type(encrypted_payload) is not str:
            raise TypeError("encrypted_payload is not a string.")

        if type(signature) is not str:
            raise TypeError("signature is not a string.")

        if type(encrypted_crypto_data) is not str:
            raise TypeError("encrypted_crypto_data is not a string.")

        # decrypt and decode crypto data
        try:
            decrypted_crypto_data = wc.rsa_decrypt(
                self.private_key, encrypted_crypto_data)

            key, iv = decrypted_crypto_data.split("|")
        except Exception as e:
            raise DecryptCryptoDataException(e)

        # verify signature
        try:
            wc.verify_signature(self.public_key, signature,
                                decrypted_crypto_data)
        except ValueError as e:
            raise SignatureDoesNotMatchException()
        except Exception as e:
            raise SignatureVerificationException(e)

        # decrypt payload
        try:
            payload = wc.aes_decrypt(key, iv, encrypted_payload)
        except Exception as e:
            raise DecryptPayloadException(e)

        # done!

        return payload
