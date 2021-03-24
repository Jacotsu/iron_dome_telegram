#!/usr/bin/env python3
import random
import logging
import json
import sys
from os import makedirs
from datetime import datetime
from time import sleep
from telethon import TelegramClient, sync, errors
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import InputChannel
from telegram.ext import DelayQueue
from utils import filter_emojis, init_settings, stringify_user_dict, \
    stringify_user


str_ftime_str = '%d-%m-%Y@%H:%M:%S'
logging_level = logging.INFO
settings_file_path = 'settings.json'
data_path = 'infiltrators'
fail_threshold = 5
# 1 request per second
requests_wait_time = 1

logging.basicConfig(
    level=logging_level,
    format='%(asctime)s| %(message)s'
)
logging.getLogger('telethon').setLevel(level=logging.INFO)
logger = logging.getLogger()


def process_group(group_entity):
    infiltrators = 0
    try:
        # The user passed a group id and hash
        if isinstance(group_entity, list):
            group = InputChannel(group_entity[0], group_entity[1])
        else:
            group = client.get_input_entity(group_entity)
    except Exception as e:
        logger.error(e)
        return 0

    group_full = client(
        GetFullChannelRequest(channel=group)
    )

    target_group_dict = {
        'last_update': datetime.now(),
        'id': group_full.chats[0].id,
        'access_hash': group_full.chats[0].access_hash,
        'title': filter_emojis(group_full.chats[0].title),
        'members': []
    }

    try:
        with open(f'{data_path}/{target_group_dict["id"]}.json', 'r') as\
                target_group_file:
            target_group_dict['members'] = \
                json.load(target_group_file)['members']
    except FileNotFoundError:
        pass

    participants = client.get_participants(group, aggressive=True)

    for part in participants:
        processed = False
        while not processed:
            try:
                full_part = client(GetFullUserRequest(part))
                if part.id not in settings['user_exceptions'] and not part.bot\
                   and full_part.about:
                    logger.debug(
                        f'{stringify_user(part)}: {full_part.about}'
                    )
                    if any(trigger_word in data_field.casefold()
                           for data_field in [
                               full_part.about,
                               full_part.first_name,
                               full_part.last_name,
                               full_part.username
                           ]
                           for trigger_word in settings['trigger_words']):

                        member = {
                            'id': part.id,
                            'access_hash': part.access_hash,
                            'first_name': filter_emojis(part.first_name),
                            'last_name': filter_emojis(part.last_name),
                            'about': full_part.about,
                            'username': part.username,
                            'phone': part.phone
                        }

                        for old_member in target_group_dict['members']:
                            if member['id'] == old_member['id']:
                                target_group_dict['members'].remove(old_member)
                                break
                        target_group_dict['members'].append(member)
                        logger.info(
                            'Found possible infiltrator: '
                            f'{stringify_user_dict(member)} '
                            f'\"{member["about"]}\"'
                        )
                        infiltrators += 1
                processed = True
            except errors.FloodWaitError as e:
                logger.error(f'Rate limit triggered, waiting {e.seconds}s')
                sleep(e.seconds + 3.0)
            except Exception as e:
                logger.error(e)
            except KeyboardInterrupt as e:
                with open(
                    f'{data_path}/{target_group_dict["id"]}.json', 'w') as\
                        target_group_file:
                    json.dump(target_group_dict, target_group_file, indent=4,
                              default=str)
                raise e
            sleep(requests_wait_time)

    with open(f'{data_path}/{target_group_dict["id"]}.json', 'w') as\
            target_group_file:
        json.dump(target_group_dict, target_group_file, indent=4,
                  default=str)

    return infiltrators


if __name__ == '__main__':
    total_infiltrators = 0
    total_groups_scraped = 0
    start_time = datetime.now()

    makedirs(data_path, exist_ok=True)
    settings = init_settings(settings_file_path)
    logger.debug(f'Settings loaded: {settings}')

    with TelegramClient('iron_dome', settings['api_id'],
                        settings['api_hash']) as client:
        settings['user_exceptions'].append(client.get_me().id)

        try:
            for group_entity in settings['groups_to_preserve']:
                processed = False
                fail_count = 0
                while not processed:
                    try:
                        number_of_infiltrators = process_group(group_entity)
                        total_infiltrators += number_of_infiltrators
                        total_groups_scraped += 1
                        processed = True
                    except errors.FloodWaitError as e:
                        logger.error('Rate limit triggered, waiting '
                                     f'{e.seconds}s')
                        sleep(e.seconds + 3.0)
                    except Exception as e:
                        logger.error(e)
                        fail_count += 1

                    if fail_count > fail_threshold:
                        logger.error(f'could not process group {group_entity}')
                        break
                    sleep(requests_wait_time)
        except KeyboardInterrupt:
            pass
        finally:
            time_delta = datetime.now() - start_time
            logger.info('Statistics')
            logger.info(f'Total groups analyzed: {total_groups_scraped}')
            logger.info(f'Total infiltrators found: {total_infiltrators}')
            logger.info(f'Total time: {time_delta}')
