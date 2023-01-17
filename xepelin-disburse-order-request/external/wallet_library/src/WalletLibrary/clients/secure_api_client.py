import json
import requests

from typing import Any, Dict

from ..constants.crypto import EMPTY_BODY_STRING, ENCRYPTION_HEADER, SIGNATURE_HEADER

from ..exceptions.crypto.missing_key_exception import MissingKeyException
from ..exceptions.crypto.missing_private_key_passphrase_exception import MissingPrivateKeyPassphraseException
from ..exceptions.request.http_error_exception import HttpErrorException
from ..exceptions.response.bad_json_received_exception import BadJsonReceivedException
from ..exceptions.response.crypto_header_missing_exception import CryptoHeaderMissingException
from ..exceptions.response.malformed_body_exception import MalformedBodyException
from ..exceptions.response.signature_header_missing_exception import SignatureHeaderMissingException
from ..exceptions.response.unexpected_empty_body_received_exception import UnexpectedEmptyBodyReceivedException
from ..exceptions.unknown_api_exception import UnknownApiException

from ..services.crypto_service import CryptoService


class SecureApiClient:
    """Base class in charge of handling communication with Wallet using encryption and cryptographic signature.
    This class must not be used directly. Instead, your client should inherit from it."""

    def __init__(self,  base_url, prefix="", private_key=None, passphrase=None, public_key=None, use_encryption=True):
        """SecureApiClient constructor

        Args:
            base_url (str): Wallet's url, e.g. https://wallet.xepelin.com.
            prefix (str, optional): Service prefix, e.g. "accounts". Defaults to "".
            private_key (str, optional):  Service's private key (*). Defaults to None.
            passphrase (str, optional): Private key's passphrase (*). Defaults to None.
            public_key (str, optional): Wallet's public key (*). Defaults to None.
            use_encryption (bool, optional): Whether to use encryption or not (**). Defaults to True.

        (*) Encryption will always be enabled in Staging, RC, and Production, rendering this params mandatory.
        (**) Encryption can only be disabled in QA and local, otherwise the communication with Wallet will fail.

        Raises:
            TypeError: If any of the params is of the wrong type.
            MissingKeyException: A public and/or private key was expected but not provided.
            MissingPrivateKeyPassphraseException: A passphrase for the private key was expected but not provided.
        """

        if type(base_url) is not str:
            raise TypeError("base_ur must be a string.")

        if type(prefix) is not str:
            raise TypeError("if provided, prefix must be a string.")

        if private_key and type(private_key) is not str:
            raise TypeError("if provided, private_key must be a string.")

        if passphrase and type(passphrase) is not str:
            raise TypeError("if provided, passphrase must be a string.")

        if public_key and type(public_key) is not str:
            raise TypeError("if provided, public_key must be a string.")

        if type(use_encryption) is not bool:
            raise TypeError("use_encryption must be a boolean.")

        if use_encryption:
            if not private_key:
                raise MissingKeyException("private")

            if not passphrase:
                raise MissingPrivateKeyPassphraseException()

            if not public_key:
                raise MissingKeyException("public")

            self.crypto_service = CryptoService(
                private_key, passphrase, public_key)

        self.base_url = base_url
        self.use_encryption = use_encryption
        self.prefix = prefix

    def build_url(self, path=""):
        """Builds an URL using base_url and prefix

        Args:
            path (str, optional): Endpoint path without service prefix, e.g. for "/accounts/balance", it would be just "balance". Defaults to "".

        Returns:
            str: the complete endpoint path, including the prefix.
        """
        if path == "":
            return self.prefix

        if self.prefix == "":
            return path

        return f"{self.prefix}/{path}"

    def secure_request(self, url, method, params=None, payload=None, empty_body_expected=False):
        """Executes a request to Wallet. It encrypts and signs the request and then decrypts and verifies the response if encryption is enabled.

        Args:
            url (str): path to the endpoint, without prefix. 
            method (str): HTTP method, e.g. POST
            params (Dict[str, Any], optional): Query params. Defaults to None.
            payload (Dict[str, Any], optional): Body of the request. Defaults to None.
            empty_body_expected (bool, optional): Wether an empty body is expected from Wallet. Defaults to False.

        Raises:
            UnknownApiException: There was a problem communicating with Wallet's API.
            HttpErrorException: Wrapper for "requests" library exceptions.
            BadJsonReceivedException: Wallet sent invalid JSON.
            MalformedBodyException: Body of the response does not follow the expected format (only applies when encryption is enabled).
            SignatureHeaderMissingException: Wallet didn't send tha cryptographic signature (only applies when encryption is enabled).
            CryptoHeaderMissingException: Wallet didn't send the encrypted key and iv required for decrypting the body of the response.
            UnexpectedEmptyBodyReceivedException: An empty body was received when a payload was expected.

        Returns:
            Dict[str, Any] | str: The response from Wallet, decrypted if encryption is enabled.
        """
        if self.use_encryption:
            if payload is None:
                payload = EMPTY_BODY_STRING
            else:
                payload = json.dumps(payload)

            encrypted_payload = self.crypto_service.encrypt_and_sign(
                payload)

            body = encrypted_payload["encrypted_body"]
            headers = {
                SIGNATURE_HEADER: encrypted_payload["signature_header"],
                ENCRYPTION_HEADER: encrypted_payload["encryption_header"],
            }
        else:
            body = payload
            headers = {}

        url = f"{self.base_url}/{self.build_url(url)}"

        try:
            response = requests.request(method.upper(
            ), url, params=params, headers=headers, json=body)
        except Exception as e:
            raise UnknownApiException(e)

        if response.status_code >= 400:
            raise HttpErrorException(url, response.status_code)

        if not self.use_encryption:
            return response.text

        try:
            json_response = response.json()
        except Exception as e:
            raise BadJsonReceivedException(True, e)

        try:
            encrypted_payload = json_response["encryptedPayload"]
        except Exception as e:
            raise MalformedBodyException(e)

        headers = response.headers

        try:
            signature = headers[SIGNATURE_HEADER]
        except Exception as e:
            raise SignatureHeaderMissingException()

        try:
            encrypted_crypto_data = headers[ENCRYPTION_HEADER]
        except Exception as e:
            raise CryptoHeaderMissingException()

        payload = self.crypto_service.decrypt_and_verify(
            encrypted_payload, signature, encrypted_crypto_data)

        if not payload:
            raise UnexpectedEmptyBodyReceivedException()

        if payload == EMPTY_BODY_STRING:
            if not empty_body_expected:
                raise UnexpectedEmptyBodyReceivedException()

            return ""

        try:
            payload = json.loads(payload)
        except Exception as e:
            raise BadJsonReceivedException(False, e)

        return payload
