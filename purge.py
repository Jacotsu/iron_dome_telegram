#!/usr/bin/env python3
import logging
import json
from pathlib import Path
from os import makedirs
from datetime import datetime
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
# 60 requests per second
requests_wait_time = 1/8


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

    with TelegramClient('session_name', settings['api_id'],
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
                    if user not in banned_users:
                        # This removes duplicates
                        hostile_dict[user['id']] = user

        for h_id, hostile in hostile_dict.items():
            for group in settings['groups_to_preserve']:

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

                        processed = True
                    except errors.FloodWaitError as e:
                        logger.error('Rate limit triggered, waiting '
                                     f'{e.seconds}s')
                        sleep(e.seconds + 3.0)
                    except Exception as e:
                        logger.error(e)
                        fail_count += 1

                    if fail_count > fail_threshold:
                        logger.error(
                            f'could not ban {stringify_user_dict(hostile)}'
                        )
                        break
                    sleep(requests_wait_time)

            banned_users.append(hostile['id'])
            logger.info(f'Banned {stringify_user_dict(hostile)}')

        with open(banned_file_path, 'w') as banned_file:
            json.dump(banned_users, banned_file)

    time_delta = datetime.now() - start_time
    logger.info('Statistics')
    logger.info(f'Users banned in this session: {len(hostile_dict)}')
    logger.info(f'Total users banned: {len(banned_users)}')
    logger.info(f'Total time: {time_delta}')
