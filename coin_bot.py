import hashlib
import socks
import os
import re
import asyncio
import aiohttp

from telethon import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest

REG_CODE_TOKEN = r'data-code=\"(?P<code>[^\"]+)\".+token=\"(?P<token>[^\"]+)\"'


def get_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


class DialogLogic:
    def __init__(self, client, dialog):
        self.client = client
        self.dialog = dialog

    async def send_msg(self, msg):
        await self.client.send_message(self.dialog.name, msg)

    async def get_last_msg(self):
        return (await self.client.get_messages(self.dialog, limit=1))[0]

    async def is_sorry_msg(self, msg):
        if not re.search(r'Sorry', msg.message):
            return False

        print("Найдено Sorry")
        await asyncio.sleep(60 * 3)
        return True

    async def is_wait_msg(self, msg):
        wait_time = re.findall(
            r'.+?stay.+?([\d]+) seconds',
            msg.message
        )

        if not wait_time:
            return False

        sleep_time = int(wait_time[0])
        print(f"Спим {sleep_time} секунд")
        await asyncio.sleep(sleep_time)
        return True

    async def get_visit_message(self):
        await asyncio.sleep(1)
        last_msg = await self.get_last_msg()

        await self.send_msg("/visit")

        while True:
            await asyncio.sleep(1)
            current_msg = await self.get_last_msg()

            if current_msg.id != last_msg.id:
                break

        return current_msg

    async def skip_task(self, msg):
        print('Skip captcha')

        if msg.reply_markup is None:
            print("SKIP FAILED:", msg)
            return

        rows = msg.reply_markup.rows
        if len(rows) < 2 or len(rows[1].buttons) < 2:
            print("SKIP FAILED:", msg)
            return

        await self.client(
            GetBotCallbackAnswerRequest(
                self.dialog,
                msg.id,
                data=rows[1].buttons[1].data
            )
        )

    async def url_proceed(self, msg):

        if len(msg.reply_markup.rows) <= 0:
            print("Failed find msg:", msg)
            return
        elif len(msg.reply_markup.rows[0].buttons) <= 0:
            print("Failed find msg:", msg)
            return

        url = msg.reply_markup.rows[0].buttons[0].url

        print("Найдена ссылка:", url)

        async with aiohttp.ClientSession() as session:
            text = ''
            try:
                resp = await session.get(url)
                if resp.status == 200:
                    text = await resp.text()
            except Exception:
                pass

            await asyncio.sleep(2)
            await self.is_wait_msg(
                await self.get_last_msg()
            )

            if 'captcha' in text:
                await self.skip_task(msg)
                return

            match = re.search(REG_CODE_TOKEN, text)

            if not match:
                return

            xdata = {
                "code": match.group('code'),
                "token": match.group('token')
            }

            print("Send xdata:", xdata)

            try:
                rsp = await session.post(
                    'https://dogeclick.com/reward',
                    data={
                        "code": match.group('code'),
                        "token": match.group('token')
                    }
                )
                print(await rsp.text())
            except Exception as e:
                print("SEND EXCEPTION:", e, type(e))

    async def run(self):
        me = await self.client.get_me()
        print(f'Run dialog "{self.dialog.name}" for "{me.username}" client')

        last_message_text = None
        count_double_text = 0

        while True:
            msg = await self.get_visit_message()

            if await self.is_sorry_msg(msg):
                continue

            text = msg.message

            if last_message_text == text:
                print("Найдено повторение сообщения")
                count_double_text += 1
                await self.skip_task(msg)
                await asyncio.sleep(5)
                continue
            else:
                count_double_text = 0

            last_message_text = text

            if count_double_text > 3:
                raise Exception('Превышено кол-во повторений сообщения')

            try:
                await self.url_proceed(msg)
            except Exception as e:
                print("Url proceed error:", e)

            await asyncio.sleep(5)


class CoinBot:
    def __init__(self, api_id, api_hash, chat_names, phone, password):
        self.api_id = api_id
        self.api_hash = api_hash
        self.chat_names = chat_names
        self.phone = phone
        self.password = password
        _hash = get_hash(f'{self.phone}_{self.password}')

        if not os.path.isdir('./sessions'):
            os.mkdir('./sessions')

        self.session = f'./sessions/{_hash}.session'
        # http://free-proxy.cz/ru/proxylist/country/all/socks5/ping/all
        # proxy = (socks.SOCKS5, "198.27.75.152", 1080)
        # proxy = (socks.SOCKS5, "5.133.197.203", 24382)
        self.client = None

    def client_init(self, proxy):
        print(f'Started "{self.phone}" client')
        kwargs = {
            "phone": self.phone
        }

        self.client = TelegramClient(
            self.session,
            self.api_id,
            self.api_hash,
            proxy=proxy
        )        

        if self.password is not None:
            kwargs['password'] = self.password

        self.client.start(**kwargs)
        print(f'Start client success')

    async def get_dialogs(self):
        dialogs = []
        for dlg in await self.client.get_dialogs():
            if dlg.title in self.chat_names:

                gl = DialogLogic(self.client, dlg)
                dialogs.append(gl)

        return dialogs

    async def run(self):
        dialogs = await self.get_dialogs()
        await asyncio.gather(*[
            dlg.run()
            for dlg in dialogs
        ])
