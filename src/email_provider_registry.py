import logging
from typing import Any, Dict, Optional, Type
from src.email_connector import EmailConnector

logger = logging.getLogger(__name__)

class EmailProviderRegistry:
    _providers: Dict[str, Type[EmailConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_class: Type[EmailConnector]) -> None:
        cls._providers[name.lower()] = connector_class
        logger.info(f"Registered provider: {name}")

    @classmethod
    def get(cls, name: str, config: Optional[Dict[str, Any]] = None) -> EmailConnector:
        name_lower = name.lower()
        if name_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(f"Provider '{name}' not found. Available: {available}")
        
        connector_class = cls._providers[name_lower]
        config = config or {}
        
        if name_lower == "mock":
            return connector_class(emails=config.get("emails"))
        return connector_class(**config)

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        return name.lower() in cls._providers

from src.email_connector import MockEmailConnector
EmailProviderRegistry.register("mock", MockEmailConnector)

from src.gmail_email_connector import GmailEmailConnector
EmailProviderRegistry.register("gmail", GmailEmailConnector)
