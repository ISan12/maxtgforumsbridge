from pathlib import Path
import aiosqlite

class Database:
    def __init__(self, path: str):
        self.path = path

    async def init(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS chat_topics (
                    max_chat_id INTEGER PRIMARY KEY,
                    telegram_chat_id INTEGER NOT NULL,
                    telegram_thread_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    is_group INTEGER NOT NULL DEFAULT 0
                )
            ''')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS message_map (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    max_chat_id INTEGER NOT NULL,
                    max_message_id INTEGER,
                    telegram_chat_id INTEGER NOT NULL,
                    telegram_message_id INTEGER NOT NULL,
                    direction TEXT NOT NULL
                )
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_map_max
                ON message_map(max_chat_id, max_message_id)
            ''')
            await db.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_map_tg
                ON message_map(telegram_chat_id, telegram_message_id)
            ''')
            await db.commit()

    async def get_topic(self, max_chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT telegram_chat_id, telegram_thread_id, title, is_group "
                "FROM chat_topics WHERE max_chat_id = ?",
                (max_chat_id,),
            )
            return await cur.fetchone()

    async def save_topic(self, max_chat_id, telegram_chat_id, thread_id, title, is_group):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO chat_topics "
                "(max_chat_id, telegram_chat_id, telegram_thread_id, title, is_group) "
                "VALUES (?, ?, ?, ?, ?)",
                (max_chat_id, telegram_chat_id, thread_id, title, int(is_group)),
            )
            await db.commit()

    async def get_chat_by_topic(self, telegram_chat_id: int, thread_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT max_chat_id FROM chat_topics "
                "WHERE telegram_chat_id = ? AND telegram_thread_id = ?",
                (telegram_chat_id, thread_id),
            )
            row = await cur.fetchone()
            return row[0] if row else None

    async def save_message(self, max_chat_id, max_message_id,
                           telegram_chat_id, telegram_message_id, direction):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO message_map "
                "(max_chat_id, max_message_id, telegram_chat_id, "
                "telegram_message_id, direction) VALUES (?, ?, ?, ?, ?)",
                (max_chat_id, max_message_id, telegram_chat_id,
                 telegram_message_id, direction),
            )
            await db.commit()

    async def get_telegram_message(self, max_chat_id: int, max_message_id: int):
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT telegram_chat_id, telegram_message_id "
                "FROM message_map WHERE max_chat_id = ? AND max_message_id = ? "
                "ORDER BY id DESC LIMIT 1",
                (max_chat_id, max_message_id),
            )
            return await cur.fetchone()
