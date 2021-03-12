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
from utils import init_settings, stringify_user_dict

str_ftime_str = '%d-%m-%Y@%H:%M:%S'
logging_format = '%(asctime)s| %(message)s'
logging_level = logging.INFO
settings_file_path = 'settings.json'
banned_path = 'banned'
data_path = 'data'
log_path = 'logs'
fail_threshold = 5
# 4 bans per second
average_requests_wait_time = 1/4
cool_down_limit = 300
cool_down_time = 13*60 + 22


def purge_hostiles(hostile_dict):
    ban_count = 0
    try:
        for group in settings['groups_to_preserve']:
            banned_users = []
            # Necessary to avoid useless requests about the group information
            # Telethon should cache this, but it doesn't
            try:
                group = client.get_input_entity(group)
            except errors.FloodWaitError as e:
                logger.error(
                    'Rate limit triggered, waiting '
                    f'{timedelta(seconds=e.seconds)}')
                sleep(e.seconds)
                group = client.get_input_entity(group)

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
                processed = False
                fail_count = 0
                while not processed:
                    try:
                        user = InputPeerUser(
                            hostile['id'], hostile['access_hash']
                        )
                        client.edit_permissions(
                            group, user, view_messages=False
                        )

                        banned_users.append(hostile['id'])
                        ban_count += 1
                        logger.info(f'Banned {stringify_user_dict(hostile)}')
                        processed = True
                    except errors.FloodWaitError as e:
                        logger.error(
                            'Rate limit triggered, waiting '
                            f'{timedelta(seconds=e.seconds)}')
                        sleep(e.seconds)
                        continue
                    except Exception as e:
                        logger.error(e)
                        fail_count += 1

                    if fail_count > fail_threshold:
                        logger.error(
                            f'could not ban {stringify_user_dict(hostile)}'
                        )
                        break
                    if ban_count % cool_down_limit == 0:
                        logger.info(
                            'Cooling down in order to avoid flood limit, wait'
                            f' {timedelta(seconds=cool_down_time)}'
                        )
                        sleep(cool_down_time)
                    sleep(average_requests_wait_time)

            with open(
                f'{banned_path}/{group.channel_id}.json', 'w'
            ) as banned_file:
                json.dump(banned_users, banned_file)
    except KeyboardInterrupt:
        pass
    finally:
        return ban_count


if __name__ == '__main__':
    makedirs(log_path, exist_ok=True)
    makedirs(banned_path, exist_ok=True)
    logging.basicConfig(
        filename=f'{log_path}/{datetime.now().strftime(str_ftime_str)}.log',
        format=logging_format,
        level=logging_level
    )
    logger = logging.getLogger()
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter(logging_format))
    sh.setLevel(logging_level)
    logger.addHandler(sh)

    settings = init_settings(settings_file_path)
    start_time = datetime.now()

    with TelegramClient('iron_dome', settings['api_id'],
                        settings['api_hash']) as client:
        hostile_dict = {}
        pathlist = Path(data_path).rglob('*.json')
        for path in pathlist:
            with open(path, 'r') as group_of_hostiles_file:
                hostile_group = json.load(group_of_hostiles_file)
                for user in hostile_group['members']:
                    # This removes duplicates
                    hostile_dict[user['id']] = user

        ban_count = purge_hostiles(hostile_dict)

    time_delta = datetime.now() - start_time
    logger.info('Statistics')
    logger.info(f'Bans in this session: {ban_count}')
    logger.info(f'Total time: {time_delta}')
