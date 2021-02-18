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
logging_level = logging.INFO
settings_file_path = 'settings.json'
banned_file_path = 'banned.json'
data_path = 'data'
log_path = 'logs'
fail_threshold = 5
# 3.2 bans per second
average_requests_wait_time = 1/4


def purge_hostiles(hostile_dict):
    banned_users_count = 0
    try:
        for group in settings['groups_to_preserve']:
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

            for h_id, hostile in hostile_dict.items():
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
                        banned_users_count += 1
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
                    sleep(average_requests_wait_time)
    except KeyboardInterrupt:
        pass
    finally:
        return banned_users_count


if __name__ == '__main__':
    makedirs(log_path, exist_ok=True)
    logging.basicConfig(
        filename=f'{log_path}/{datetime.now().strftime(str_ftime_str)}.log'
    )
    logger = logging.getLogger()
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(logging_level)

    settings = init_settings(settings_file_path)
    start_time = datetime.now()

    with TelegramClient('iron_dome', settings['api_id'],
                        settings['api_hash']) as client:
        banned_users = []
        try:
            with open(banned_file_path, 'r') as banned_file:
                banned_users = json.load(banned_file)
        except FileNotFoundError:
            pass

        hostile_dict = {}
        pathlist = Path(data_path).rglob('*.json')
        for path in pathlist:
            with open(path, 'r') as group_of_hostiles_file:
                hostile_group = json.load(group_of_hostiles_file)
                for user in hostile_group['members']:
                    if user['id'] not in banned_users:
                        # This removes duplicates
                        hostile_dict[user['id']] = user

        banned_users_count = purge_hostiles(hostile_dict)
        with open(banned_file_path, 'w') as banned_file:
            json.dump(banned_users, banned_file)

    time_delta = datetime.now() - start_time
    logger.info('Statistics')
    logger.info(f'Users banned in this session: {banned_users_count}')
    logger.info(f'Total users banned: {len(banned_users)}')
    logger.info(f'Total time: {time_delta}')
