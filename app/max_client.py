from pathlib import Path
from pymax import Client, ExtraConfig, Message

class MaxClient:
    def __init__(self, phone: str, work_dir: str, session_name: str):
        Path(work_dir).mkdir(parents=True, exist_ok=True)
        self.client = Client(
            phone=phone,
            work_dir=work_dir,
            session_name=session_name,
            extra_config=ExtraConfig(
                reconnect=True,
                reconnect_delay=3,
            ),
        )

    def on_message(self, handler):
        @self.client.on_message()
        async def _handler(message: Message, client: Client):
            await handler(message, client)

    def on_message_edit(self, handler):
        @self.client.on_message_edit()
        async def _handler(message: Message, client: Client):
            await handler(message, client)

    def on_message_delete(self, handler):
        @self.client.on_message_delete()
        async def _handler(event, client: Client):
            await handler(event, client)

    async def start(self):
        await self.client.start()

    async def send_text(self, chat_id: int, text: str, reply_to=None):
        return await self.client.send_message(
            chat_id=chat_id,
            text=text,
            reply_to=reply_to,
        )

    async def get_user_name(self, user_id):
        if user_id is None:
            return "Unknown"
        user = await self.client.get_user(user_id)
        if user is None or not user.names:
            return str(user_id)
        n = user.names[0]
        return n.name or " ".join(x for x in (n.first_name, n.last_name) if x) or str(user_id)

    async def get_chat(self, chat_id: int):
        return await self.client.get_chat(chat_id)

    @property
    def me_id(self):
        if self.client.me is None:
            return None
        return self.client.me.contact.id
