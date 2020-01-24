
import aiohttp
import asyncio
import json
import socks
import re

from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector


RE_PROXY = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,6}'


class ProxyObject:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = int(port)

    def get_tuple(self):
        return socks.SOCKS5, self.ip, self.port

    def get_str(self):
        return f'socks5://{self.ip}:{self.port}'

    def __str__(self):
        return f'{self.ip}:{self.port}'

    async def check_url(self, url):
        try:
            connector = ProxyConnector.from_url(self.get_str())
            async with aiohttp.ClientSession(connector=connector) as _sess:
                response = await _sess.get(url, timeout=1)
                if response.status == 200:
                    return True
        except Exception as e:
            # print("ER:", type(e), e)
            pass

        return False


class ProxyManager:
    def __init__(self,  test_url):
        self.test_url = test_url
        self.queue_proxys = asyncio.Queue()

        loop = asyncio.get_event_loop()
        loop.create_task(self.load_loop())

    async def load_loop(self):
        while True:
            if self.queue_proxys.empty():
                await self.load_proxys()

            await asyncio.sleep(10)

    async def load_proxys(self):
        print("run load proxy")

        url = 'https://api.proxyscrape.com/?request=share&proxytype=socks5&timeout=1000&country=all'
        async with aiohttp.ClientSession() as _sess:
            response = await _sess.get(url)
            if response.status != 200:
                raise Exception(f'Failed request to "{url}" url')

            url = str(response.url).replace(
                'https://textitor.com/',
                'https://api.textitor.com/'
            ) + '/plain'

            response = await _sess.get(url)
            if response.status != 200:
                raise Exception(f'Failed request to "{url}" url')

            text = await response.text()

        proxys = []

        for line in re.findall(RE_PROXY, text):
            sp = line.split(':')
            if len(sp) != 2:
                continue
            proxy = ProxyObject(sp[0], sp[1])
            proxys.append(proxy)

        print(f'find {len(proxys)} proxys')

        while len(proxys) > 0:
            batch_proxys = proxys[:20]
            proxys = proxys[20:]            

            checked = await asyncio.gather(*[
                proxy.check_url(self.test_url)
                for proxy in batch_proxys
            ])

            print(f'checked {len(checked)} proxys')

            for i, proxy in enumerate(batch_proxys):
                if checked[i]:
                    self.queue_proxys.put_nowait(proxy)

    async def get_proxy(self):
        return await self.queue_proxys.get()
