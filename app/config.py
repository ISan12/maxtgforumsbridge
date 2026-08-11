from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    max_phone: str
    telegram_token: str
    telegram_forum_chat_id: int
    max_work_dir: str
    max_session_name: str
    db_path: str
    log_level: str

def load_config() -> Config:
    phone = os.getenv("MAX_PHONE", "").strip()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    forum_id = os.getenv("TELEGRAM_FORUM_CHAT_ID", "").strip()
    if not phone:
        raise RuntimeError("MAX_PHONE is not set")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")
    if not forum_id:
        raise RuntimeError("TELEGRAM_FORUM_CHAT_ID is not set")
    return Config(
        max_phone=phone,
        telegram_token=token,
        telegram_forum_chat_id=int(forum_id),
        max_work_dir=os.getenv("MAX_WORK_DIR", "data/max"),
        max_session_name=os.getenv("MAX_SESSION_NAME", "account.db"),
        db_path=os.getenv("DB_PATH", "data/bridge.sqlite3"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
