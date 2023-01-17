import os


def get_from_environment(key, default_value):
    try:
        return os.environ[key]
    except KeyError:
        return default_value

SO_API_URL="https://eompkh218070xfg.m.pipedream.net"
SO_API_UPDATE_INVOICE_PATH="api/erp/update-invoice-status-by-id"
SO_API_TOKEN="Bearer test-token"

WALLET_URL="https://eomzfl1jvs1av6g.m.pipedream.net"
WALLET_USE_ENCRYPTION="false"
WALLET_PRIVATE_KEY=""
WALLET_PUBLIC_KEY=""
WALLET_PASSPHRASE="xepelin123"

default_config = {
    "server_global": {
        "url": get_from_environment("SO_API_URL", SO_API_URL),
        "update_invoice_path": get_from_environment("SO_API_UPDATE_INVOICE_PATH", SO_API_UPDATE_INVOICE_PATH),
        "token": get_from_environment("SO_API_TOKEN", SO_API_TOKEN),
    },
    "wallet": {
        "url": get_from_environment("WALLET_URL", WALLET_URL),
        "use_encryption": get_from_environment("WALLET_USE_ENCRYPTION", WALLET_USE_ENCRYPTION) == "true",
        "private_key": get_from_environment("WALLET_PRIVATE_KEY", WALLET_PRIVATE_KEY),
        "public_key": get_from_environment("WALLET_PUBLIC_KEY", WALLET_PUBLIC_KEY),
        "passphrase": get_from_environment("WALLET_PASSPHRASE", WALLET_PASSPHRASE),
    },
}
