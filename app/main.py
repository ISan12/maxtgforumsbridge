import asyncio,logging
from aiogram import Bot,Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from .config import load_config
from .database import Database
from .max_client import MaxClient
from .topics import TopicManager
from .bridge import Bridge
from .commands import Commands

async def main():
    cfg=load_config()
    logging.basicConfig(level=getattr(logging,cfg.log_level,logging.INFO),format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    db=Database(cfg.db_path); await db.init()
    session=AiohttpSession(proxy=cfg.telegram_proxy) if cfg.telegram_proxy else None
    bot=Bot(token=cfg.telegram_token,session=session,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp=Dispatcher()
    maxc=MaxClient(cfg); topics=TopicManager(bot,db,cfg.forum_chat_id)
    bridge=Bridge(bot,db,topics,maxc,cfg); commands=Commands(bot,db,topics,maxc,cfg)

    maxc.on_message(bridge.max_to_tg)
    maxc.on_edit(bridge.max_edit)
    maxc.on_delete(bridge.max_delete)

    @dp.message()
    async def all_messages(message):
        if (message.text or "").startswith("/"):
            await commands.dispatch(message)
        await bridge.telegram_to_max(message)

    # Critical: MAX auth is completed before Telegram polling starts.
    await maxc.start()
    await topics.service_topic()
    from .formatting import startup
    await topics.service_message(startup())
    await dp.start_polling(bot,allowed_updates=list(Update.model_fields.keys()))

if __name__=="__main__":
    asyncio.run(main())
