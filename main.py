import asyncio
import argparse
import os
import json

from coin_bot import CoinBot

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


async def wait_exit():
    while True:
        await asyncio.sleep(0.1)


async def main():
    # runing all bots
    tasks = [wait_exit()] + [bot.run() for bot in bots]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    # runing main
    loop = asyncio.get_event_loop()    
    loop.run_until_complete(main())
