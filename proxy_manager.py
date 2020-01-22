import re
import time
import aiohttp
import asyncio


class ProxyObject:
    def __init__(self, ip, port, code):
        self.ip = ip
        self.port = port
        self.code = code

    def __str__(self):
        return f'{self.ip}:{self.port}[{self.code}]'

    def get_settings(self):
        return {
            "http": f'http://{self.ip}:{self.port}',
            "https": f'https://{self.ip}:{self.port}',
            "ftp": f'ftp://{self.ip}:{self.port}'
        }

    async def test_url(self, url, timeout=1):
        try:
            async with aiohttp.ClientSession() as sess:
                resp = await sess.get(
                    url,
                    timeout=timeout,
                    proxy=self.get_settings()
                )
                if resp.status == 200:
                    print("success")
                    return True
        except Exception as e:
            # pass
            print(e)

        return False


class ProxyManager:
    def __init__(self, test_proxy_url):
        self.test_proxy_url = test_proxy_url
        self.proxys = []
        self.proxy_idx = 0
        self.timeout_success = 1

    async def load_proxyes(self):
        print('run getting proxyes')

        async with aiohttp.ClientSession() as sess:
            # https://pypi.org/project/aiohttp-socks/
            # http://free-proxy.cz/ru/proxylist/country/all/socks5/ping/all
            resp = await sess.get(
                'https://free-proxy-list.net/',
                timeout=10,
            )
            if resp.status == 200:
                text = await resp.text()
            else:
                raise Exception('Proxy getter not valid =(')

        print('succes')

        data = [
            list(filter(None, i))[0]
            for i in re.findall(
                r'<td class="hm">(.*?)</td>|<td>(.*?)</td>',
                text
            )
        ]
        groupings = [
            dict(
                zip(
                    ['ip', 'port', 'code', 'using_anonymous'],
                    data[i:i+4]
                )
            ) for i in range(0, len(data), 4)
        ]

        self.proxys.clear()

        _proxys = []
        for x in groupings:
            ip = x.get('ip', '')
            port = x.get('port', '')
            code = x.get('code', '')
            using_anonymous = x.get('using_anonymous', '')

            if not re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip):
                continue

            if not re.match(r'\d{1,5}', port):
                continue

            proxy = ProxyObject(ip, port, code)
            print(proxy)
            _proxys.append(proxy)

        proxy_check = await asyncio.gather(*[
            px.test_url(self.test_proxy_url, self.timeout_success)
            for px in _proxys
        ])

        self.proxys = [x for i, x in enumerate(_proxys) if proxy_check[i]]

        print('Load proxys:', len(self.proxys))

    async def get_next_proxy(self):
        if len(self.proxys) == 0:
            await self.load_proxyes()

        print('Get next proxy')
        proxy = self.proxys[self.proxy_idx]
        self.proxy_idx += 1

        print('self.proxy_idx:', self.proxy_idx)
        print('len(self.proxys):', len(self.proxys))

        if len(self.proxys) <= self.proxy_idx:
            self.proxy_idx = 0
            await self.load_proxyes()

        return proxy
