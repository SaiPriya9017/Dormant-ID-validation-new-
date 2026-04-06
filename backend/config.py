"""Configuration management for Cloudant retrieval system."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # Cloudant API Configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "")
    API_KEY = os.getenv("API_KEY", "")
    API_PASSWORD = os.getenv("API_PASSWORD", "")
    
    # Application Settings
    DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
    CHECKPOINT_DIR = Path(os.getenv("CHECKPOINT_DIR", "./checkpoints"))
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "5000"))
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS = 3
    REQUEST_TIMEOUT = 30
    
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL is required")
        if not cls.API_KEY:
            raise ValueError("API_KEY is required")
        if not cls.API_PASSWORD:
            raise ValueError("API_PASSWORD is required")
        return True

config = Config()

# Made with Bob
