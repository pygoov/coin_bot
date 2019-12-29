import hashlib
import socks
import os

from telethon import TelegramClient


def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


class CoinBot:
    def __init__(self, chat_name, api_id, api_hash):
        self.chat_name = chat_name
        self.api_id = api_id
        self.api_hash = api_hash
        _hash = get_hash(self.api_id + self.api_hash)

        if not os.path.isdir('./sessions'):
            os.mkdir('./sessions')

        self.session = f'./sessions/{_hash}.session'
        # http://free-proxy.cz/ru/proxylist/country/all/socks5/ping/all
        # proxy = (socks.SOCKS5, "192.169.202.106", 33731)
        proxy = (socks.SOCKS5, "5.133.197.203", 24382)
        self.client = TelegramClient(
            self.session,
            self.api_id,
            self.api_hash,
            proxy=proxy
        )

    async def run(self):
        print(f' ====== RUN {self.chat_name} bot ======')

        print('run started')
        await self.client.start()
        print('started success')

        for dlg in await self.client.get_dialogs():
            print(dlg.name)
