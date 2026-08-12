from pathlib import Path
from pymax import Client, ExtraConfig

class MaxClient:
    def __init__(self,cfg):
        Path(cfg.max_work_dir).mkdir(parents=True,exist_ok=True)
        self.client=Client(
            phone=cfg.max_phone,
            work_dir=cfg.max_work_dir,
            session_name=cfg.max_session_name,
            extra_config=ExtraConfig(reconnect=True,reconnect_delay=3,log_level=cfg.pymax_log_level),
        )

    def on_message(self,fn):
        @self.client.on_message()
        async def h(event,client): await fn(event,client)

    def on_edit(self,fn):
        @self.client.on_message_edit()
        async def h(event,client): await fn(event,client)

    def on_delete(self,fn):
        @self.client.on_message_delete()
        async def h(event,client): await fn(event,client)

    async def start(self): await self.client.start()
    @property
    def me_id(self): return self.client.me.contact.id if self.client.me else None
    async def chat(self,chat_id): return await self.client.get_chat(chat_id)
    async def user(self,user_id): return await self.client.get_user(user_id)
    async def user_name(self,user_id):
        if user_id is None: return "Unknown"
        u=await self.user(user_id)
        if u is None or not u.names: return str(user_id)
        n=u.names[0]
        return n.name or " ".join(x for x in (n.first_name,n.last_name) if x) or str(user_id)
    async def send_text(self,chat_id,text,reply_to=None):
        return await self.client.send_message(chat_id=chat_id,text=text,reply_to=reply_to)
    async def send_attachment(self,chat_id,text,attachment,reply_to=None):
        return await self.client.send_message(chat_id=chat_id,text=text,attachments=[attachment],reply_to=reply_to)
    async def search_by_phone(self,phone): return await self.client.search_by_phone(phone)
    def dm_id(self,a,b): return self.client.get_chat_id(first_user_id=a,second_user_id=b)
    async def join_group(self,url): return await self.client.join_group(url)
