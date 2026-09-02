"""
Email Agent Factory

Creates EmailAgent instances with the email provider configured in .env

Usage:
    from src.agent_factory import create_email_agent
    
    agent = create_email_agent()
    # agent.process_unread_emails()
"""

import logging

from dotenv import load_dotenv

from src.email_connector import EmailConnector
connector = create_email_agent()
from src.email_provider_registry import EmailProviderRegistry

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def create_email_agent() -> EmailAgent:
    """
    Create EmailAgent with provider configured via .env
    
    Reads:
        EMAIL_PROVIDER - which provider to use (mock, gmail, yahoo, outlook)
        EMAIL_CREDENTIALS_PATH - path to credentials file
        BUSINESS_ID - unique business identifier
        LOG_LEVEL - logging level
    
    Returns:
        Configured EmailAgent instance
    
    Raises:
        ValueError: If provider not registered or credentials missing
    
    Example:
        agent = create_email_agent()
        emails = agent.fetch_unread_emails()
    """
    
    # Read configuration from .env
    provider_name = os.getenv("EMAIL_PROVIDER", "mock")
    credentials_path = os.getenv("EMAIL_CREDENTIALS_PATH")
    business_id = os.getenv("BUSINESS_ID", "default")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    # Set logging level
    logging.basicConfig(level=getattr(logging, log_level))
    
    logger.info(f"Creating EmailAgent with provider: {provider_name}")
    
    # Validate provider is registered
    if not EmailProviderRegistry.is_registered(provider_name):
        available = ", ".join(EmailProviderRegistry.list_providers())
        raise ValueError(
            f"Provider '{provider_name}' not registered. "
            f"Available: {available}"
        )
    
    # For Gmail/Yahoo/Outlook, credentials path is required
    if provider_name in ["gmail", "yahoo", "outlook"]:
        if not credentials_path:
            raise ValueError(
                f"EMAIL_CREDENTIALS_PATH required for {provider_name} provider"
            )
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}"
            )
    
    # Create connector with credentials
    connector = EmailProviderRegistry.get(
        provider_name,
        config={"credentials_path": credentials_path} if credentials_path else {}
    )
    
    logger.info(f"Connector created: {connector.__class__.__name__}")
    
    # Create and return agent
    agent = EmailAgent(connector=connector)
    logger.info(f"EmailAgent ready (business_id: {business_id})")
    
    return agent


if __name__ == "__main__":
    # Example usage
    agent = create_email_agent()
    print(f"Agent ready: {agent}")
    # emails = agent.fetch_unread_emails()
    # print(f"Unread emails: {len(emails)}")