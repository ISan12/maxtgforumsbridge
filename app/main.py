import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from .bridge import Bridge
from .config import load_config
from .database import Database
from .max_client import MaxClient
from .telegram import TelegramBridge

async def main():
    cfg = load_config()
    logging.basicConfig(
        level=getattr(logging, cfg.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    db = Database(cfg.db_path)
    await db.init()

    # Если задан TELEGRAM_PROXY — используем его для подключения к Bot API.
    # Поддерживаются: socks5://user:pass@host:port, http://host:port
    session = AiohttpSession(proxy=cfg.telegram_proxy) if cfg.telegram_proxy else None
    bot = Bot(
        token=cfg.telegram_token,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    max_client = MaxClient(
        cfg.max_phone, cfg.max_work_dir, cfg.max_session_name
    )

    telegram = TelegramBridge(
        bot, db, max_client, cfg.telegram_forum_chat_id
    )
    bridge = Bridge(bot, db, max_client, telegram)

    max_client.on_message(bridge.max_message)
    max_client.on_message_edit(bridge.max_message_edit)
    max_client.on_message_delete(bridge.max_message_delete)

    dp.include_router(telegram.router)

    async def run_telegram():
        # Ждём, пока MAX завершит авторизацию (введён SMS-код, сессия сохранена, login выполнен) — только после этого запускаем Telegram polling
	# Без этого таймаут подключения к Telegram API отменял соседний таск через asyncio.gather(), прерывая asyncio.to_thread(input, …) при вводе SMS-кода и вызывая:
        # CancelledError → SSL APPLICATION_DATA_AFTER_CLOSE_NOTIFY
        await max_client.ready.wait()
        await dp.start_polling(bot)

    try:
        await asyncio.gather(
            max_client.start(),
            run_telegram(),
        )
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
