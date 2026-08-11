import logging

log = logging.getLogger(__name__)

class Bridge:
    def __init__(self, bot, db, max_client, telegram_bridge):
        self.bot = bot
        self.db = db
        self.max = max_client
        self.telegram = telegram_bridge

    async def max_message(self, message, client):
        try:
            await self.telegram.send_max_message(message, client)
        except Exception:
            log.exception("Failed to forward MAX message %s", getattr(message, "id", None))

    async def max_message_edit(self, message, client):
        if message.chat_id is None:
            return
        mapped = await self.db.get_telegram_message(message.chat_id, message.id)
        if not mapped:
            return
        tg_chat_id, tg_message_id = mapped
        try:
            await self.bot.edit_message_text(
                chat_id=tg_chat_id,
                message_id=tg_message_id,
                text=(message.text or "✏️")[:4096],
            )
        except Exception:
            log.exception("Failed to edit Telegram message for MAX %s", message.id)

    async def max_message_delete(self, event, client):
        chat_id = getattr(event, "chat_id", None)
        message_ids = getattr(event, "message_ids", None)
        if chat_id is None or not message_ids:
            return

        for max_message_id in message_ids:
            mapped = await self.db.get_telegram_message(chat_id, max_message_id)
            if not mapped:
                continue
            tg_chat_id, tg_message_id = mapped
            try:
                await self.bot.delete_message(tg_chat_id, tg_message_id)
            except Exception:
                log.exception("Failed to delete Telegram message for MAX %s", max_message_id)
