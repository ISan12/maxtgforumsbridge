import logging

from .formatting import attachment_notice, chat_message

log = logging.getLogger(__name__)


class Bridge:
    def __init__(self, bot, db, topics, maxc, cfg):
        self.bot = bot
        self.db = db
        self.topics = topics
        self.max = maxc
        self.cfg = cfg

    @staticmethod
    def max_reply_id(message):
        for name in ("reply_to", "reply_to_message", "reply_message"):
            value = getattr(message, name, None)

            if isinstance(value, int):
                return value

            if value is not None and getattr(value, "id", None) is not None:
                return value.id

        return None

    async def max_to_tg(self, message, client):
        if message.chat_id is None:
            return

        if (
            message.sender is not None
            and message.sender == self.max.me_id
        ):
            return

        try:
            chat = await self.max.chat(message.chat_id)

            if chat is None:
                return

            is_group = bool(getattr(chat, "is_group", False))
            title = (
                getattr(chat, "title", None)
                or await self.max.user_name(message.sender)
            )

            tg_chat_id, thread_id = await self.topics.ensure(
                message.chat_id,
                title,
                is_group,
            )

            reply_tg_id = None
            reply_max_id = self.max_reply_id(message)

            if reply_max_id is not None:
                mapped = await self.db.by_max(
                    message.chat_id,
                    reply_max_id,
                )

                if mapped:
                    reply_tg_id = mapped[1]

            text = message.text or ""

            if is_group:
                sender = await self.max.user_name(message.sender)
                text = chat_message(sender, text, True)

            if not message.attaches:
                if not text:
                    return

                sent = await self.bot.send_message(
                    chat_id=tg_chat_id,
                    message_thread_id=thread_id,
                    text=text[:4096],
                    reply_to_message_id=reply_tg_id,
                )

            else:
                label = "📎 <b>Вложение из MAX</b>"

                types = {
                    type(item).__name__
                    for item in message.attaches
                }

                if any("PhotoAttachment" in x for x in types):
                    label = "🖼️ <b>Фото из MAX</b>"
                elif any("VideoAttachment" in x for x in types):
                    label = "🎥 <b>Видео из MAX</b>"
                elif any("FileAttachment" in x for x in types):
                    label = "📄 <b>Файл из MAX</b>"

                body = f"{label}"
                if text:
                    body += f"\n\n{text}"

                sent = await self.bot.send_message(
                    chat_id=tg_chat_id,
                    message_thread_id=thread_id,
                    text=body[:4096],
                    reply_to_message_id=reply_tg_id,
                )

            await self.db.save_message(
                message.chat_id,
                message.id,
                tg_chat_id,
                sent.message_id,
                "max_to_telegram",
            )

        except Exception:
            log.exception(
                "MAX -> Telegram failed for message %s",
                getattr(message, "id", None),
            )

    async def telegram_to_max(self, message):
        if message.chat.id != self.cfg.forum_chat_id:
            return

        if message.from_user and message.from_user.is_bot:
            return

        thread_id = message.message_thread_id

        if thread_id is None:
            return

        max_chat_id = await self.db.chat_by_topic(
            message.chat.id,
            thread_id,
        )

        if max_chat_id is None:
            return

        try:
            reply_to = None

            if message.reply_to_message:
                mapped = await self.db.by_tg(
                    message.chat.id,
                    message.reply_to_message.message_id,
                )

                if mapped and mapped[0] == max_chat_id:
                    reply_to = mapped[1]

            sender = (
                message.from_user.full_name
                if message.from_user
                else "Telegram"
            )

            text = message.text or message.caption

            if not text:
                media = (
                    message.photo
                    or message.video
                    or message.video_note
                    or message.voice
                    or message.audio
                    or message.document
                )

                if not media:
                    return

                text = "📎 Медиа из Telegram"

            outgoing = chat_message(sender, text, True)

            sent = await self.max.send_text(
                max_chat_id,
                outgoing,
                reply_to=reply_to,
            )

            await self.db.save_message(
                max_chat_id,
                getattr(sent, "id", None),
                message.chat.id,
                message.message_id,
                "telegram_to_max",
            )

        except Exception:
            log.exception(
                "Telegram -> MAX failed for message %s",
                message.message_id,
            )

            try:
                await message.reply(
                    "❌ Не получилось отправить сообщение в MAX."
                )
            except Exception:
                pass

    async def max_edit(self, message, client):
        if message.chat_id is None:
            return

        mapped = await self.db.by_max(
            message.chat_id,
            message.id,
        )

        if not mapped:
            return

        try:
            await self.bot.edit_message_text(
                chat_id=mapped[0],
                message_id=mapped[1],
                text=(message.text or "✏️")[:4096],
            )
        except Exception:
            log.exception("MAX edit failed")

    async def max_delete(self, event, client):
        chat_id = getattr(event, "chat_id", None)

        if chat_id is None:
            return

        for message_id in (getattr(event, "message_ids", None) or []):
            mapped = await self.db.by_max(chat_id, message_id)

            if not mapped:
                continue

            try:
                await self.bot.delete_message(
                    chat_id=mapped[0],
                    message_id=mapped[1],
                )
            except Exception:
                log.exception(
                    "MAX delete failed for %s",
                    message_id,
                )
