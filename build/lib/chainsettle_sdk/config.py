from pydantic import Extra
from typing import ClassVar

from functools import lru_cache
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings():
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    STORE_SALT_API_KEY: str = os.getenv("STORE_SALT_API_KEY")

    ZERO_ADDRESS: ClassVar[str] = "0x0000000000000000000000000000000000000000"

    # ChainSettle Configuration
    CHAINSETTLE_API_URL: ClassVar[str] = os.getenv(
        "CHAINSETTLE_API_URL",
        "http://localhost:5045"
    )
    CHAINSETTLE_AKASH_URL: ClassVar[str] = os.getenv(
        "CHAINSETTLE_AKASH_URL",
        "https://gdvsns5685f696ufl48m643lc4.ingress.akash-palmito.org"
    )

    # ChainSettle Contract Addresses
    CHAINSETTLE_SETTLEMENT_REGISTRY: ClassVar[str] = os.getenv(
        "CHAINSETTLE_SETTLEMENT_REGISTRY",
        "0x64af6d4C1f2bC29E6f24750A8c0aF85af132734e"
    )

    # Supported enums
    CHAINSETTLE_SUPPORTED_NETWORKS: ClassVar[List[str]] = ["ethereum", "blockdag", "base"]
    CHAINSETTLE_SUPPORTED_APIS: ClassVar[List[str]] = ["plaid", "github", "paypal", "docusign"]
    CHAINSETTLE_SUPPORTED_JURISDICTIONS: ClassVar[List[str]] = ["us", "uk", "eu", "pa", "mx", "ng", "other"]
    CHAINSETTLE_SUPPORTED_ASSET_CATEGORIES: ClassVar[List[str]] = [
        "real_estate", "private_credit", "commodity", "other"
    ]

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

@lru_cache()
def get_settings() -> Settings:
    return Settings()
