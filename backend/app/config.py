"""Application configuration loaded from environment variables."""
import os


def _load_dotenv() -> None:
    """Load a local .env file if python-dotenv is unavailable we do a tiny parse."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def _as_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Runtime settings for the PolicyPilot AI backend."""

    def __init__(self) -> None:
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.gemini_temperature: float = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
        self.enable_demo_mode: bool = _as_bool(os.getenv("ENABLE_DEMO_MODE", "false"))
        origins = os.getenv(
            "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
        )
        self.cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]

    @property
    def ai_mode(self) -> str:
        """Human readable description of the currently active AI mode."""
        if self.gemini_api_key:
            return "live"
        if self.enable_demo_mode:
            return "demo"
        return "unconfigured"


settings = Settings()
