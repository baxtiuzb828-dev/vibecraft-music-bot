import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_path: Path
    sponsor_channels: tuple[str, ...]
    admin_contact: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "put-your-telegram-bot-token-here":
        raise RuntimeError("Set BOT_TOKEN in the .env file before starting the bot.")

    channels = tuple(
        channel.strip()
        for channel in os.getenv("SPONSOR_CHANNELS", "").split(",")
        if channel.strip()
    )
    return Settings(
        bot_token=token,
        database_path=Path(os.getenv("DATABASE_PATH", "data/music_bot.sqlite3")),
        sponsor_channels=channels,
        admin_contact=os.getenv("ADMIN_CONTACT", "").strip().lstrip("@"),
    )