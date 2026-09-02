"""
Email Provider Registry

Manages registration and instantiation of email connectors.
This allows the agent to support multiple email providers (Gmail, Yahoo, Outlook, etc.)
without modifying the core agent logic.

Usage:
    EmailProviderRegistry.register('gmail', GmailEmailConnector)
    connector = EmailProviderRegistry.get('gmail', config)
"""

import logging
from typing import Any, Dict, Optional, Type
from src.email_connector import EmailConnector

logger = logging.getLogger(__name__)


class EmailProviderRegistry:
    """
    Registry for email provider connectors.
    Supports dynamic registration and instantiation of different email services.
    """

    # Registered providers: name -> connector class
    _providers: Dict[str, Type[EmailConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_class: Type[EmailConnector]) -> None:
        """
        Register an email provider connector.

        Args:
            name: Provider name (e.g., 'gmail', 'yahoo', 'outlook')
            connector_class: EmailConnector subclass

        Example:
            EmailProviderRegistry.register('gmail', GmailEmailConnector)
        """
        if not issubclass(connector_class, EmailConnector):
            raise TypeError(
                f"{connector_class.__name__} must inherit from EmailConnector"
            )

        cls._providers[name.lower()] = connector_class
        logger.info(f"Registered email provider: {name}")

    @classmethod
    def get(cls, name: str, config: Optional[Dict[str, Any]] = None) -> EmailConnector:
        """
        Get an instantiated connector for the given provider.

        Args:
            name: Provider name (e.g., 'gmail', 'yahoo', 'outlook', 'mock')
            config: Configuration dict for the connector (credentials, etc.)

        Returns:
            EmailConnector instance

        Raises:
            ValueError: If provider not registered

        Example:
            config = {
                'credentials_path': '/path/to/credentials.json',
                'business_id': '123'
            }
            connector = EmailProviderRegistry.get('gmail', config)
        """
        name_lower = name.lower()

        if name_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Email provider '{name}' not registered. "
                f"Available: {available or 'none'}"
            )

        connector_class = cls._providers[name_lower]
        config = config or {}

        logger.info(f"Instantiating {name} connector")
        
        # MockEmailConnector takes 'emails' parameter, not 'credentials_path'
        if name_lower == "mock":
            return connector_class(emails=config.get("emails"))
        
        return connector_class(**config)

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        List all registered providers.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """
        Check if a provider is registered.

        Args:
            name: Provider name

        Returns:
            True if registered, False otherwise
        """
        return name.lower() in cls._providers

    @classmethod
    def unregister(cls, name: str) -> None:
        """
        Unregister a provider (mainly for testing).

        Args:
            name: Provider name
        """
        name_lower = name.lower()
        if name_lower in cls._providers:
            del cls._providers[name_lower]
            logger.info(f"Unregistered email provider: {name}")


def register_builtin_providers() -> None:
    """
    Register built-in email providers.
    Called on module import to set up default providers.
    """
    from src.email_connector import MockEmailConnector

    EmailProviderRegistry.register("mock", MockEmailConnector)
    logger.info("Built-in providers registered")


# Auto-register built-in providers
register_builtin_providers()