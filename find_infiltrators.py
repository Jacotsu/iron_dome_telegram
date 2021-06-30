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

logging.basicConfig(
    level=logging_level,
    format='%(asctime)s| %(message)s'
)
logging.getLogger('telethon').setLevel(level=logging.INFO)
logger = logging.getLogger()


async def process_group(group_entity):
    infiltrators = 0
    # The user passed a channel dict
    if isinstance(group_entity, dict):
        try:
            group = InputChannel(
                group_entity['group_id'],
                group_entity['group_hash']
            )
        except KeyError:
            group = await client.get_input_entity(group_entity['url'])
    else:
        group = await client.get_input_entity(group_entity)

    group_full = await client(
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

    participants = await client.get_participants(group, aggressive=True)

    for part in participants:
        try:
            full_part = await client(GetFullUserRequest(part))
            if part.id not in settings['user_exceptions'] and not part.bot\
               and full_part.about:
                logger.debug(
                    f'{stringify_user(part)}: {full_part.about}'
                )
                if any(trigger_word in data_field.casefold()
                       if data_field else None
                       for data_field in [
                           full_part.about,
                           part.first_name,
                           part.last_name,
                           part.username
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
        except KeyboardInterrupt as e:
            with open(
                f'{data_path}/{target_group_dict["id"]}.json', 'w') as\
                    target_group_file:
                json.dump(target_group_dict, target_group_file, indent=4,
                          default=str, ensure_ascii=False)
            raise e

    with open(f'{data_path}/{target_group_dict["id"]}.json', 'w') as\
            target_group_file:
        json.dump(target_group_dict, target_group_file, indent=4,
                  default=str, ensure_ascii=False)

    return infiltrators


async def main(settings, client):
    total_infiltrators = 0
    total_groups_scraped = 0
    start_time = datetime.now()

    current_user = await client.get_me()
    settings['user_exceptions'].append(current_user.id)

    try:
        for group_entity in settings['groups_to_preserve']:
            number_of_infiltrators = await process_group(group_entity)
            total_infiltrators += number_of_infiltrators
            total_groups_scraped += 1
    except KeyboardInterrupt:
        pass
    finally:
        time_delta = datetime.now() - start_time
        logger.info('Statistics')
        logger.info(f'Total groups analyzed: {total_groups_scraped}')
        logger.info(f'Total infiltrators found: {total_infiltrators}')
        logger.info(f'Total time: {time_delta}')

if __name__ == '__main__':
    makedirs(data_path, exist_ok=True)
    settings = init_settings(settings_file_path)
    logger.debug(f'Settings loaded: {settings}')

    with TelegramClient(
        'iron_dome', settings['api_id'], settings['api_hash'],
        flood_sleep_threshold=86400, base_logger='telethon'
    ) as client:
        client.loop.run_until_complete(main(settings, client))
