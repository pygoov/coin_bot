import asyncio
import argparse
import os
import json

from coin_bot import CoinBot
from proxy_manager import ProxyManager


async def wait_exit():
    while True:
        await asyncio.sleep(0.1)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--config-file', '-c',
        type=str,
        default='./config.json'
    )

    args = parser.parse_args()
    config_file = args.config_file

    if not os.path.isfile(config_file):
        raise Exception(f'File "{config_file} not fount"')

    with open(args.config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)

    # creating bots from config
    bots = [
        CoinBot(
            config_data['api_id'],
            config_data['api_hash'],
            config_data['chat_names'],
            cfg['phone'],
            cfg['password']
        )
        for cfg in config_data['clients']
    ]

    proxy_manager = ProxyManager('https://api.telegram.org')

    while True:
        tasks = []

        for bot in bots:
            bot.client_init(
                await proxy_manager.get_next_proxy()
            )
            tasks.append(bot.run())

        try:
            # runing all bots
            await asyncio.gather(*tasks)
        except Exception as e:
            print('Exception:', e)

        await asyncio.sleep(60)


if __name__ == "__main__":
    # runing main
    loop = asyncio.get_event_loop()
    loop.create_task(wait_exit())
    loop.run_until_complete(main())
