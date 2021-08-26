#!/usr/bin/env python3
import logging
import json
import random
from pathlib import Path
from os import makedirs
from datetime import datetime, timedelta
from time import sleep
from telethon import TelegramClient, sync, errors
from telethon.tl.types import InputPeerUser
from telethon.errors.rpcbaseerrors import BadRequestError
from utils import init_settings, stringify_user_dict

str_ftime_str = '%d-%m-%Y@%H:%M:%S'
logging_format = '%(asctime)s| %(message)s'
logging_level = logging.INFO
settings_file_path = 'settings.json'
banned_path = 'banned'
data_path = 'data'
log_path = 'logs'

cool_down_limit = 300
cool_down_time = 13*60 + 22

logging.basicConfig(
        filename=f'{log_path}/{datetime.now().strftime(str_ftime_str)}.log',
        format=logging_format,
        level=logging_level
    )
logging.getLogger('telethon').setLevel(level=logging.INFO)
logger = logging.getLogger()
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter(logging_format))
sh.setLevel(logging_level)
logger.addHandler(sh)


async def purge_hostiles(hostile_dict):
    ban_count = ban_attempts = 0
    try:
        for group in settings['groups_to_preserve']:
            banned_users = []
            group = await client.get_input_entity(group)

            try:
                with open(
                    f'{banned_path}/{group.channel_id}.json', 'r'
                ) as banned_file:
                    banned_users = json.load(banned_file)
            except FileNotFoundError:
                pass

            for h_id, hostile in hostile_dict.items():
                # Skip already banned users
                if h_id in banned_users:
                    continue

                ban_attempts += 1
                user = InputPeerUser(
                    hostile['id'], hostile['access_hash']
                )
                try:
                    await client.edit_permissions(
                        group, user, view_messages=False
                    )
                except BadRequestError as e:
                    logger.error(f"{e} while processing: {hostile} ")
                    continue

                banned_users.append(hostile['id'])
                ban_count += 1
                logger.info(f'Banned {stringify_user_dict(hostile)}')

                if ban_attempts % cool_down_limit == 0:
                    logger.info(
                        'Cooling down in order to avoid flood limit, wait'
                        f' {timedelta(seconds=cool_down_time)}'
                    )
                    sleep(cool_down_time)

            with open(
                f'{banned_path}/{group.channel_id}.json', 'w'
            ) as banned_file:
                json.dump(banned_users, banned_file)
    except KeyboardInterrupt:
        pass
    finally:
        return ban_count


async def main(settings, client):
    hostile_dict = {}
    start_time = datetime.now()
    pathlist = Path(data_path).rglob('*.json')
    for path in pathlist:
        with open(path, 'r') as group_of_hostiles_file:
            try:

                hostile_group = json.load(group_of_hostiles_file)
            except json.decoder.JSONDecodeError:
                logger.error(f"Error while processing {path}", exc_info=True)

            for user in hostile_group['members']:
                # This removes duplicates
                hostile_dict[user['id']] = user

    ban_count = await purge_hostiles(hostile_dict)
    time_delta = datetime.now() - start_time
    logger.info('Statistics')
    logger.info(f'Bans in this session: {ban_count}')
    logger.info(f'Total time: {time_delta}')


if __name__ == '__main__':
    makedirs(log_path, exist_ok=True)
    makedirs(banned_path, exist_ok=True)
    settings = init_settings(settings_file_path)

    with TelegramClient(
            'iron_dome', settings['api_id'], settings['api_hash'],
            flood_sleep_threshold=86400, base_logger='telethon'
    ) as client:
        client.loop.run_until_complete(main(settings, client))
