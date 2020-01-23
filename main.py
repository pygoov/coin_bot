import asyncio
import argparse
import os
import json
import linecache
import sys
import traceback

from coin_bot import CoinBot
from proxy import ProxyManager
from datetime import datetime
from io import StringIO


def traceback_msg(e):
    exc_type, exc_obj, first_tb = sys.exc_info()
    tb = StringIO()
    traceback.print_tb(first_tb, file=tb)
    sp_tab = '  '
    msg_ex = '''
==========Exception===========
Message:
>>>
{e}
<<<
Time: {time}
Traceback:
{tb}=============================='''.format(
        e=sp_tab + str(e).replace('\n', '\n' + sp_tab),
        time=datetime.now(),
        tb=tb.getvalue()
    )
    return msg_ex


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

    proxy_manager = ProxyManager()

    while True:
        run_tasks = []

        await proxy_manager.load_proxys()

        print('run init bots')
        for bot in bots:
            proxy = await proxy_manager.get_proxy('https://api.telegram.org')
            await bot.client_init(proxy)
            run_tasks.append(bot.run())

        try:
            # runing all bots
            print('run all bots')
            await asyncio.gather(*run_tasks)
        except Exception as e:
            print(traceback_msg(e))

        await asyncio.sleep(60)


if __name__ == "__main__":
    # runing main
    loop = asyncio.get_event_loop()
    loop.create_task(wait_exit())
    loop.create_task(main())
    loop.run_forever()
