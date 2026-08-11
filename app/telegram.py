from aiogram import Bot, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

class TelegramBridge:
    def __init__(self, bot: Bot, db, max_client, forum_chat_id: int):
        self.bot = bot
        self.db = db
        self.max = max_client
        self.forum_chat_id = forum_chat_id
        self.router = Router()
        self.router.message.register(self.start, CommandStart())
        self.router.message.register(self.on_message)

    async def start(self, message: Message):
        await message.answer(
            "maxtgforumsbridge is running.\n"
            "Пиши сообщения в соответствующих темах форума."
        )

    async def ensure_topic(self, max_chat_id: int, title: str, is_group: bool):
        existing = await self.db.get_topic(max_chat_id)
        if existing:
            return existing[0], existing[1]

        topic = await self.bot.create_forum_topic(
            chat_id=self.forum_chat_id,
            name=(title or f"MAX {max_chat_id}")[:128],
        )
        await self.db.save_topic(
            max_chat_id,
            self.forum_chat_id,
            topic.message_thread_id,
            (title or f"MAX {max_chat_id}")[:128],
            is_group,
        )
        return self.forum_chat_id, topic.message_thread_id

    async def send_max_message(self, message, client):
        if message.chat_id is None:
            return
        if message.sender is not None and message.sender == self.max.me_id:
            return

        chat = await self.max.get_chat(message.chat_id)
        if chat is None:
            return

        title = chat.title or await self.max.get_user_name(message.sender)
        tg_chat_id, thread_id = await self.ensure_topic(
            message.chat_id, title, chat.is_group
        )

        text = message.text or ""
        if message.attaches:
            text = (text + "\n\n📎 MAX: сообщение содержит вложение.").strip()
        if not text:
            return

        if chat.is_group:
            text = f"{await self.max.get_user_name(message.sender)}: {text}"

        sent = await self.bot.send_message(
            chat_id=tg_chat_id,
            message_thread_id=thread_id,
            text=text[:4096],
        )
        await self.db.save_message(
            message.chat_id, message.id, tg_chat_id, sent.message_id,
            "max_to_telegram",
        )

    async def on_message(self, message: Message):
        if message.chat.id != self.forum_chat_id:
            return
        if message.from_user and message.from_user.is_bot:
            return
        thread_id = message.message_thread_id
        if thread_id is None:
            return

        max_chat_id = await self.db.get_chat_by_topic(message.chat.id, thread_id)
        if max_chat_id is None:
            return

        text = message.text or message.caption
        if not text:
            await message.reply("Пока bridge умеет отправлять обратно только текст.")
            return

        sender = message.from_user.full_name if message.from_user else "Telegram"
        outgoing = f"{sender}: {text}"
        sent = await self.max.send_text(max_chat_id, outgoing)

        await self.db.save_message(
            max_chat_id, getattr(sent, "id", None),
            message.chat.id, message.message_id, "telegram_to_max",
        )
