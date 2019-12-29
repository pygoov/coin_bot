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
        cfg['chat_name'],
        cfg['api_id'],
        cfg['api_hash']
    )
    for cfg in config_data
]


async def main():
    # runing all bots
    await asyncio.gather(*[bot.run() for bot in bots])


if __name__ == "__main__":
    # runing main
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
