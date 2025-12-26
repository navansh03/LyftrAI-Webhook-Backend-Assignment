import os


class Config:
    """Application configuration loaded from environment variables."""
    
    def __init__(self):
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:////data/app.db")
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")

        self._validate()
    
    def _validate(self) -> None:
        """Validate required configuration. Raises RuntimeError if invalid."""
        if not self.WEBHOOK_SECRET:
            raise RuntimeError("WEBHOOK_SECRET environment variable is required and cannot be empty")
    
    def get_database_path(self) -> str:
        """Extract SQLite file path from DATABASE_URL.
        
        Expects format: sqlite:////path/to/file.db
        Returns: /path/to/file.db
        """
        prefix = "sqlite:///"
        if not self.DATABASE_URL.startswith(prefix):
            raise RuntimeError(f"DATABASE_URL must start with '{prefix}'")
        return self.DATABASE_URL[len(prefix):]


def get_config() -> Config:
    """Create and return a validated Config instance."""
    return Config()