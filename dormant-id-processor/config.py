"""Configuration management for Dormant-ID processor."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration."""
    
    # API Endpoints
    TOKEN_URL = os.getenv("TOKEN_URL", "")
    USERS_API_URL = os.getenv("USERS_API_URL", "")
    BLUEPAGES_API_URL = os.getenv("BLUEPAGES_API_URL", "")
    
    # API Credentials
    CLIENT_ID = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
    
    # Processing Settings
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))
    CONCURRENCY = int(os.getenv("CONCURRENCY", "5"))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    # Directories
    INPUT_DIR = Path(os.getenv("INPUT_DIR", "./input"))
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./output"))
    CHECKPOINT_DIR = Path(os.getenv("CHECKPOINT_DIR", "./checkpoints"))
    LOG_DIR = Path(os.getenv("LOG_DIR", "./logs"))
    
    # Token Settings
    TOKEN_CACHE_DURATION = int(os.getenv("TOKEN_CACHE_DURATION", "3600"))
    
    @classmethod
    def ensure_directories(cls):
        """Create required directories if they don't exist."""
        cls.INPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        required = {
            "TOKEN_URL": cls.TOKEN_URL,
            "USERS_API_URL": cls.USERS_API_URL,
            "CLIENT_ID": cls.CLIENT_ID,
            "CLIENT_SECRET": cls.CLIENT_SECRET,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required configuration: {', '.join(missing)}\n"
                "Please check your .env file"
            )
        
        return True


# Global config instance
config = Config()

# Made with Bob
