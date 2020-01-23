
import aiohttp
import asyncio
import json
import socks
import re

from aiohttp_socks import ProxyType, ProxyConnector, ChainProxyConnector


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
                response = await _sess.get(url, timeout=2)
                if response.status == 200:
                    return True
        except Exception as e:
            # print("ER:", type(e), e)
            pass

        return False


class ProxyManager:
    def __init__(self):
        self.biffer_proxys = []
        self.proxys = []

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
            x = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{2,6}', text)

        pxs = [x.split(':') for x in text.split('\n')]
        self.biffer_proxys = [ProxyObject(x[0], x[1]) for x in pxs if len(x) == 2]
        print(f'load {len(self.proxys)} proxys')

    async def get_proxy(self, test_url):
        print('getting proxy')
        count_try = 0
        while count_try < 10:
            if len(self.proxys) == 0:
                await self.load_proxys()

            proxy = self.proxys.pop()

            if await proxy.check_url(test_url):
                print(f"Proxy {proxy} find success")
                return proxy

            await asyncio.sleep(1)

        raise Exception("Max count trys getting proxy =(")
