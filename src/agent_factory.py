import logging
import os
from dotenv import load_dotenv
from src.email_database import init_email_db
from src.email_connector import EmailConnector
from src.email_provider_registry import EmailProviderRegistry

logger = logging.getLogger(__name__)
load_dotenv()

def create_email_agent() -> EmailConnector:
    init_email_db()
    logger.info("Email database initialized")
    
    provider_name = os.getenv("EMAIL_PROVIDER", "mock")
    credentials_path = os.getenv("EMAIL_CREDENTIALS_PATH")
    
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    logger.info(f"Creating connector: {provider_name}")
    
    if provider_name in ["gmail", "yahoo", "outlook"]:
        if not credentials_path or not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials not found: {credentials_path}")
    
    connector = EmailProviderRegistry.get(
        provider_name,
        config={"credentials_path": credentials_path} if credentials_path else {}
    )
    
    logger.info(f"Connector ready: {connector.__class__.__name__}")
    return connector
