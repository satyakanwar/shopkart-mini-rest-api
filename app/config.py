import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

def setting(name, default=None):
    return os.getenv(name, default)

def azure_configured():
    return bool(setting("COSMOS_ENDPOINT") and setting("COSMOS_KEY")
                and setting("STORAGE_CONNECTION_STRING"))
