import random
import string
import time

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import SHA512, SHA1
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pkcs1_15
from Crypto.Util.Padding import pad, unpad

from base64 import b64encode, b64decode


def aes_padding():
    """Returns AED paddind block size used by this lib."""
    return 16


def load_rsa_key(key_as_string, passphrase = None):
    """Creates an RSA key from its string representation.
    Args:
        key_as_string (str): String representation of an RSA key (private or public).
        passphrase (str, optional): Passphrase in case a private key is provided. Defaults to None.
    Raises:
        TypeError: key_as_string or passphrase are not strings.
        ValueError: If key cannot be converted to an RSA key. Probably the format or the passphrase are wrong.
    Returns: 
        RSA.RsaKey: An RSA key object
    """
    if type(key_as_string) is not str:
        raise TypeError("key_as_string is not a string.")

    if passphrase and type(passphrase) is not str:
        raise TypeError("passphrase is not a string.")

    try:
        return RSA.import_key(key_as_string, passphrase)
    except Exception as e:
        raise ValueError(e)


def encode_b64(data):
    """Encode base64 and return the string representation.
    Args:
        data (bytes): Data to encode.
    Raises:
        TypeError: If data is not an instance of bytes.
    Returns:
        str: String representation of data encoded in base64.
    """
    if type(data) is not bytes:
        raise TypeError("data must be an instance of bytes.")

    return b64encode(data).decode("ascii")


def decode_b64(encoded_str):
    """Decode a base64 string and return the original data.
    Args:
        encoded_str (str): String in base64.
    Raises:
        TypeError: Encoded_str is not a string.
        ValueError: If encoded_str is not a valid base64 string.
    Returns: 
        bytes: The original data.
    """
    if type(encoded_str) is not str:
        raise TypeError("encoded_str is not a string.")

    try:
        return b64decode(encoded_str.encode("ascii"))
    except Exception as e:
        raise ValueError(e)


def string_to_bytes(s):
    """Converts a string to binary representation.
    Args:
        s (str): String to convert, in utf-8.
    Raises:
        TypeError: If s is not a string.
    Returns:
        bytes: Binary representation of s.
    """
    if type(s) is not str:
        raise TypeError("s is not a string.")

    return s.encode("utf-8")


def bytes_to_string(b):
    """Converts bytes to string representation.
    Args:
        b (bytes): Bytes to convert.
    Raises:
        TypeError: b is not a bytes object.
        ValueError: An exception occurred while converting b.
    Returns:
        str: String representation of b, in utf-8.
    """
    if type(b) is not bytes:
        raise TypeError("b is not a bytes object.")

    try:
        return b.decode("utf-8")
    except Exception as e:
        raise ValueError(e)


def generate_hash(s):
    """Calculates a cryptographic hash of a string using SHA512.
    Args:
        s (str): String to hash.
    Raises:
        TypeError: s is not a string.
    Returns:
        SHA512.SHA512Hash: The generated hash.
    """
    if type(s) is not str:
        raise TypeError("s is not a string.")

    return SHA512.new(string_to_bytes(s))


def rsa_encrypt(public_key, data):
    """Encrypts and base64 encode a string using a public key.
    Args:
        public_key (RSA.RsaKey): The public key.
        data (str): The string to encrypt. Max length is floor(n/8) - 11, n being the size of the key in bits. For example, a 1024 bits key can encrypt up to 117 bytes.
    Raises:
        TypeError: Either public_key is not an instance of RSA.RsaKey, is not a public key, or data is not a string.
        ValueError: The encryption failed, probably because data is too long.
    Returns: 
        str: The encrypted string (base64 encoded).
    """
    if type(public_key) is not RSA.RsaKey:
        raise TypeError("public_key as not an instance of RSA.RsaKey.")

    if public_key.has_private():
        raise TypeError(
            "public_key is not a public key, make sure you're not passing the private key instead.")

    if type(data) is not str:
        raise TypeError("data is not a string.")

    try:
        cipher = PKCS1_v1_5.new(public_key)

        return encode_b64(cipher.encrypt(string_to_bytes(data)))
    except Exception as e:
        raise ValueError(e)


def rsa_decrypt(private_key, data, sleep_time = 120):
    """Decrypts a base64 encoded string using a private key.
    Args:
        private_key (RSA.RsaKey): The private key.
        data (str): The string to decrypt (base64 encoded).
        sleep_time (float): Time in seconds to sleep after the decryption failed. This is used to mitigate possible timing attacks. Defaults to 120 seconds.
    Raises:
        TypeError: Either private_key is not an instance of RSA.RsaKey, is not a private key, or data is not a string.
        ValueError: The decryption failed.
    Returns:
        str: The decrypted string.
    """
    if type(private_key) is not RSA.RsaKey:
        raise TypeError("private_key is not an instance of RSA.RsaKey.")

    if not private_key.has_private():
        raise TypeError(
            "private_key is not a private key, make sure you're not passing the public key instead.")

    if type(data) is not str:
        raise TypeError("data is not a string.")

    # This is going to be upgraded to PKCS1_OAEP ASAP, but it has to be done in the node
    # library too, and then do a synchronized deploy of several services
    sentinel = ''.join(random.choice(string.ascii_letters)
                       for i in range(512))

    cipher = PKCS1_v1_5.new(private_key, SHA1)

    decrypted_data = bytes_to_string(
        cipher.decrypt(decode_b64(data), string_to_bytes(sentinel), 0))

    if decrypted_data == sentinel:
        time.sleep(sleep_time)

        raise ValueError(
            "Unknown error while trying to decrypt data. Probably the public key of private_key is not the key used for encryption.")

    return decrypted_data


def aes_encrypt(data, key = None, iv = None):
    """Encrypts a string using AES CBC.
    Args:
        data (str): Data to encrypt.
        key (str, optional): Encryption key (32 bytes, base64 encoded). Defaults to None.
        iv (str, optional): Initialization vector (16 bytes, base64 encoded). Defaults to None.
    Raises:
        TypeError: data, key, or iv are not strings.
        ValueError: AES encryption failed.
    Returns:
        (str, str, str): (encrypted data, key, iv), all base64 encoded.
    """
    if type(data) is not str:
        raise TypeError("data is not a string.")

    if key and type(key) is not str:
        raise TypeError("key is not a string.")

    if iv and type(iv) is not str:
        raise TypeError("iv is not a string.")

    if key is None:
        key = get_random_bytes(32)
    else:
        key = decode_b64(key)

    if iv is not None:
        iv = decode_b64(iv)

    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)

        encrypted_data = cipher.encrypt(
            pad(string_to_bytes(data), aes_padding()))

        return encode_b64(encrypted_data), encode_b64(key), encode_b64(cipher.iv)
    except Exception as e:
        raise ValueError(e)


def aes_decrypt(key, iv, encrypted_data):
    """Decrypts a string encrypted using AES CBC.
    Args:
        key (str): Key used for encryption (base64 encoded).
        iv (str): Initialization vector (base64 encoded).
        encrypted_data (str): The encrypted string (base64 encoded).
    Raises:
        TypeError: key, iv, or encrypted_data are not strings.
        ValueError: AES decryption failed.
    Returns:
        str: The decrypted string.
    """
    if key and type(key) is not str:
        raise TypeError("key is not a string.")

    if iv and type(iv) is not str:
        raise TypeError("iv is not a string.")

    if type(encrypted_data) is not str:
        raise TypeError("encrypted_data is not a string.")

    try:
        cipher = AES.new(decode_b64(key), AES.MODE_CBC, decode_b64(iv))

        return bytes_to_string(unpad(cipher.decrypt(decode_b64(encrypted_data)), aes_padding()))
    except Exception as e:
        raise ValueError(e)


def sign(private_key, message):
    """Generate a cryptographic signature using a private key.
    Args:
        private_key (RSA.RsaKey): The private key that will be used for signing.
        message (str): The string to sign.
    Raises:
        TypeError: Either private_key is not an instance of RSA.RsaKey, is not a private_key, or message is not a string.
        ValueError: Signature generation process failed.
    Returns: 
        str: The signature (base64 encoded).
    """
    if type(private_key) is not RSA.RsaKey:
        raise TypeError("private_key is not an instance of RSA.RsaKey.")

    if not private_key.has_private():
        raise TypeError("private_key is not private key.")

    if type(message) is not str:
        raise TypeError("message is not a string.")

    try:
        return encode_b64(pkcs1_15.new(private_key).sign(generate_hash(message)))
    except Exception as e:
        raise ValueError(e)


def verify_signature(public_key, signature, message):
    """Verify a signature using a public key and the original string.
    Args:
        public_key (RSA.RsaKey): The public key that will be used for verification.
        signature (str): The cryptographic signature (base64 encoded).
        message(str): The original message.
    Raises:
        TypeError: Either public_key is not an instance of RSA.RsaKey, is not a public key, or signature or message are not strings.
        ValueError: The signature is not valid.
    """
    if type(public_key) is not RSA.RsaKey:
        raise TypeError("public_key is not an instance of RSA.RsaKey.")

    if public_key.has_private():
        raise TypeError("public_key is not public key.")

    if type(signature) is not str:
        raise TypeError("signature is not a string.")

    if type(message) is not str:
        raise TypeError("message is not a string.")

    pkcs1_15.new(public_key).verify(
        generate_hash(message), decode_b64(signature))

