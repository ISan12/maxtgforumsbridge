from pathlib import Path
import aiosqlite

class Database:
    def __init__(self,path:str):
        self.path=path

    async def init(self):
        Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            await db.execute('CREATE TABLE IF NOT EXISTS chat_topics (max_chat_id INTEGER PRIMARY KEY, telegram_chat_id INTEGER NOT NULL, telegram_thread_id INTEGER NOT NULL, title TEXT NOT NULL, is_group INTEGER NOT NULL DEFAULT 0)')
            await db.execute('CREATE TABLE IF NOT EXISTS message_map (id INTEGER PRIMARY KEY AUTOINCREMENT, max_chat_id INTEGER NOT NULL, max_message_id INTEGER, telegram_chat_id INTEGER NOT NULL, telegram_message_id INTEGER NOT NULL, direction TEXT NOT NULL)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_mm_max ON message_map(max_chat_id,max_message_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_mm_tg ON message_map(telegram_chat_id,telegram_message_id)')
            await db.commit()

    async def get_meta(self,key):
        async with aiosqlite.connect(self.path) as db:
            c=await db.execute('SELECT value FROM meta WHERE key=?',(key,))
            r=await c.fetchone()
            return r[0] if r else None

    async def set_meta(self,key,value):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)',(key,value))
            await db.commit()

    async def get_topic(self,max_chat_id):
        async with aiosqlite.connect(self.path) as db:
            c=await db.execute('SELECT telegram_chat_id,telegram_thread_id,title,is_group FROM chat_topics WHERE max_chat_id=?',(max_chat_id,))
            return await c.fetchone()

    async def save_topic(self,max_chat_id,tg_chat_id,thread_id,title,is_group):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT OR REPLACE INTO chat_topics(max_chat_id,telegram_chat_id,telegram_thread_id,title,is_group) VALUES(?,?,?,?,?)',(max_chat_id,tg_chat_id,thread_id,title,int(is_group)))
            await db.commit()

    async def chat_by_topic(self,tg_chat_id,thread_id):
        async with aiosqlite.connect(self.path) as db:
            c=await db.execute('SELECT max_chat_id FROM chat_topics WHERE telegram_chat_id=? AND telegram_thread_id=?',(tg_chat_id,thread_id))
            r=await c.fetchone()
            return r[0] if r else None

    async def save_message(self,max_chat_id,max_message_id,tg_chat_id,tg_message_id,direction):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT INTO message_map(max_chat_id,max_message_id,telegram_chat_id,telegram_message_id,direction) VALUES(?,?,?,?,?)',(max_chat_id,max_message_id,tg_chat_id,tg_message_id,direction))
            await db.commit()

    async def by_tg(self,tg_chat_id,tg_message_id):
        async with aiosqlite.connect(self.path) as db:
            c=await db.execute('SELECT max_chat_id,max_message_id FROM message_map WHERE telegram_chat_id=? AND telegram_message_id=? ORDER BY id DESC LIMIT 1',(tg_chat_id,tg_message_id))
            return await c.fetchone()

    async def by_max(self,max_chat_id,max_message_id):
        async with aiosqlite.connect(self.path) as db:
            c=await db.execute('SELECT telegram_chat_id,telegram_message_id FROM message_map WHERE max_chat_id=? AND max_message_id=? ORDER BY id DESC LIMIT 1',(max_chat_id,max_message_id))
            return await c.fetchone()
