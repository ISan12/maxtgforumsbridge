from .formatting import service_title


class TopicManager:
    def __init__(self, bot, db, forum_id):
        self.bot = bot
        self.db = db
        self.forum_id = forum_id

    async def service_topic(self):
        saved = await self.db.get_meta("service_topic_id")
        if saved:
            return int(saved)

        topic = await self.bot.create_forum_topic(
            chat_id=self.forum_id,
            name=service_title(),
        )

        await self.db.set_meta(
            "service_topic_id",
            str(topic.message_thread_id),
        )

        return topic.message_thread_id

    async def ensure(self, max_chat_id, title, is_group):
        row = await self.db.get_topic(max_chat_id)

        if row:
            return row[0], row[1]

        topic = await self.bot.create_forum_topic(
            chat_id=self.forum_id,
            name=(title or f"MAX {max_chat_id}")[:128],
        )

        await self.db.save_topic(
            max_chat_id,
            self.forum_id,
            topic.message_thread_id,
            (title or f"MAX {max_chat_id}")[:128],
            is_group,
        )

        return self.forum_id, topic.message_thread_id

    async def service_message(self, text):
        thread = await self.service_topic()

        return await self.bot.send_message(
            chat_id=self.forum_id,
            message_thread_id=thread,
            text=text,
        )
