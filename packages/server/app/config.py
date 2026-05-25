"""Application settings.

All knobs are loaded from the environment on startup (see the rate-limit and
duration tables in ``docs/product-plan.md``). Every field has a safe local-dev
default, so ``uvicorn app.main:app`` works with no configuration at all.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database --------------------------------------------------------
    database_url: str = "sqlite:///./roomq.db"

    # --- Public base URLs used to build the links we hand out ------------
    # api_base_url is the agent-facing host: room_link = {api_base_url}/rooms/{id}
    # ui_base_url is the human viewer host: viewer  = {ui_base_url}/rooms/{id}
    api_base_url: str = "http://localhost:8000"
    ui_base_url: str = "http://localhost:3000"

    # --- CORS ------------------------------------------------------------
    # Comma-separated list of allowed browser origins (the UI host).
    cors_origins: str = "http://localhost:3000"

    # --- Admin / moderation ---------------------------------------------
    # Bearer secret for the moderation endpoints (room/message takedown).
    # Empty (the default) disables the admin routes entirely.
    admin_token: str = ""

    # --- Room duration bounds (minutes) ---------------------------------
    min_room_minutes: int = 60
    max_room_minutes: int = 300
    default_room_minutes: int = 60

    # --- Caps ------------------------------------------------------------
    max_agents_per_room: int = 20
    max_batch_size: int = 10
    max_content_bytes: int = 32 * 1024
    max_agenda_chars: int = 200

    # --- Rate limits -----------------------------------------------------
    limit_ip_rooms_per_day: int = 50
    limit_agent_msgs_per_min: int = 60
    limit_room_msgs_per_min: int = 300
    limit_room_agenda_per_min: int = 10

    # --- Long-poll (GET /rooms/{id}/wait) -------------------------------
    # How long a /wait request holds open before returning empty so the client
    # reconnects. Must stay under Cloudflare's ~100s origin timeout (524).
    wait_max_seconds: int = 90
    # How often the held request re-checks the inbox while waiting.
    wait_poll_interval_seconds: float = 1.5

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached accessor so the env is parsed exactly once per process."""
    return Settings()
