
import argparse
import os
import json

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

print(config_data)
# args.config_file.close()
