import hashlib
import secrets
from dataclasses import dataclass

from src.config.settings import settings


@dataclass(frozen=True)
class ApiKey:
    """Value object for API keys."""

    key: str

    @classmethod
    def generate(cls) -> "ApiKey":
        """Generate a new API key."""
        # Generate a 32-character random key
        key = secrets.token_urlsafe(32)
        return cls(key=key)

    def hash(self) -> str:
        """Create a hash of the API key for storage."""
        salted_key = f"{self.key}{settings.api_key_hash_salt}"
        return hashlib.sha256(salted_key.encode()).hexdigest()

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash a key string directly."""
        salted_key = f"{key}{settings.api_key_hash_salt}"
        return hashlib.sha256(salted_key.encode()).hexdigest()

    def __str__(self) -> str:
        """Return the key string."""
        return self.key

    def __repr__(self) -> str:
        """Return a safe representation that doesn't expose the key."""
        return f"ApiKey(key=***{self.key[-4:]})"