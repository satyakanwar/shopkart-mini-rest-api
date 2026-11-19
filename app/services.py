"""Lazy Azure clients. The cache prevents rebuilding clients for every request."""
from datetime import datetime, timedelta, timezone
from . import config

_cache = {}


def cosmos_database():
    if "database" not in _cache:
        from azure.cosmos import CosmosClient
        client = CosmosClient(
            config.setting("COSMOS_ENDPOINT"),
            credential=config.setting("COSMOS_KEY"),
        )
        _cache["database"] = client.get_database_client(
            config.setting("COSMOS_DATABASE", "shopkart")
        )
    return _cache["database"]


def blob_service():
    if "blob" not in _cache:
        from azure.storage.blob import BlobServiceClient
        _cache["blob"] = BlobServiceClient.from_connection_string(
            config.setting("STORAGE_CONNECTION_STRING")
        )
    return _cache["blob"]


def container(name):
    key = f"container:{name}"
    if key not in _cache:
        _cache[key] = cosmos_database().get_container_client(name)
    return _cache[key]


def create_sas_url(container_name, blob_name, permission, minutes=10):
    from azure.storage.blob import generate_blob_sas
    service = blob_service()
    account_key = getattr(service.credential, "account_key", None)
    if not account_key:
        raise RuntimeError(
            "Storage account key is unavailable; configure connection-string authentication."
        )
    token = generate_blob_sas(
        account_name=service.account_name,
        container_name=container_name,
        blob_name=blob_name,
        account_key=account_key,
        permission=permission,
        expiry=datetime.now(timezone.utc) + timedelta(minutes=minutes),
    )
    return f"{service.url.rstrip('/')}/{container_name}/{blob_name}?{token}"
