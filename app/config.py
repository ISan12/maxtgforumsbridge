from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    max_phone: str
    telegram_token: str
    forum_chat_id: int
    allowed_user_ids: frozenset[int]
    max_work_dir: str
    max_session_name: str
    db_path: str
    log_level: str
    pymax_log_level: str

def _ids(value: str) -> frozenset[int]:
    return frozenset(int(x.strip()) for x in value.split(",") if x.strip())

def load_config() -> Config:
    phone=os.getenv("MAX_PHONE","").strip()
    token=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
    forum=os.getenv("TELEGRAM_FORUM_CHAT_ID","").strip()
    if not phone or not token or not forum:
        raise RuntimeError("MAX_PHONE, TELEGRAM_BOT_TOKEN and TELEGRAM_FORUM_CHAT_ID are required")
    return Config(
        max_phone=phone,
        telegram_token=token,
        forum_chat_id=int(forum),
        allowed_user_ids=_ids(os.getenv("ALLOWED_TELEGRAM_USER_IDS","")),
        max_work_dir=os.getenv("MAX_WORK_DIR","data/max"),
        max_session_name=os.getenv("MAX_SESSION_NAME","account.db"),
        db_path=os.getenv("DB_PATH","data/bridge.sqlite3"),
        log_level=os.getenv("LOG_LEVEL","INFO").upper(),
        pymax_log_level=os.getenv("PYMAX_LOG_LEVEL","INFO").upper(),
    )
