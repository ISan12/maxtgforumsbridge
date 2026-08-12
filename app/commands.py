import logging

from .formatting import delivered_notice, help_text, send_notice, status_text
from html import escape


class Commands:
    def __init__(self, bot, db, topics, maxc, cfg):
        self.bot = bot
        self.db = db
        self.topics = topics
        self.max = maxc
        self.cfg = cfg

    def allowed(self, message):
        if message.chat.id != self.cfg.forum_chat_id:
            return False

        if not self.cfg.allowed_user_ids:
            return True

        return bool(
            message.from_user
            and message.from_user.id in self.cfg.allowed_user_ids
        )

    async def dispatch(self, message):
        if not self.allowed(message):
            return

        command = (
            (message.text or "")
            .split(maxsplit=1)[0]
            .split("@", 1)[0]
            .lower()
        )

        if command == "/start":
            await message.answer(
                "👋 <b>maxtgforumsbridge</b>\n\n"
                "Мост между MAX и Telegram.\n"
                "Напиши /help, чтобы посмотреть команды."
            )

        elif command == "/help":
            await message.answer(help_text())

        elif command == "/status":
            service_topic = await self.db.get_meta("service_topic_id")
            await message.answer(
                status_text(self.cfg.forum_chat_id, service_topic)
            )

        elif command == "/send":
            await self.send(message)

        elif command == "/join":
            await self.join(message)

    async def send(self, message):
        parts = (message.text or "").split(maxsplit=2)

        if len(parts) < 3:
            await message.answer(
                "Использование:\n"
                "<code>/send +79990000000 текст</code>"
            )
            return

        phone, text = parts[1], parts[2]

        try:
            user = await self.max.search_by_phone(phone)

            if user is None:
                await message.answer(
                    "❌ Пользователь с таким номером в MAX не найден."
                )
                return

            if user.id == self.max.me_id:
                await message.answer("❌ Нельзя отправить сообщение самому себе.")
                return

            chat_id = self.max.dm_id(self.max.me_id, user.id)
            sent = await self.max.send_text(chat_id, text)

            name = user.names[0].name if user.names else phone

            tg_chat_id, thread_id = await self.topics.ensure(
                chat_id,
                name,
                False,
            )

            notice = await self.bot.send_message(
                chat_id=tg_chat_id,
                message_thread_id=thread_id,
                text=delivered_notice(text),
            )

            await self.db.save_message(
                chat_id,
                getattr(sent, "id", None),
                tg_chat_id,
                notice.message_id,
                "send",
            )

            await message.answer(
                f"✅ <b>Готово.</b> Сообщение отправлено {escape(name)}."
            )

        except Exception:
            logging.exception("/send failed")
            await message.answer(
                "❌ Не получилось отправить сообщение.\n"
                "Подробности смотри в консоли."
            )

    async def join(self, message):
        parts = (message.text or "").split(maxsplit=1)

        if len(parts) != 2:
            await message.answer(
                "Использование:\n"
                "<code>/join https://max.ru/...</code>"
            )
            return

        try:
            chat = await self.max.join_group(parts[1].strip())
            title = getattr(chat, "title", None) or "MAX-группа"

            await message.answer(
                f"✅ <b>Готово.</b> Вступил в "
                f"<b>{escape(title)}</b>."
            )

        except Exception:
            logging.exception("/join failed")
            await message.answer(
                "❌ Не получилось вступить в MAX-группу.\n"
                "Подробности смотри в консоли."
            )
