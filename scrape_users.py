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
from telethon.tl.types import InputChannel
from telethon.errors import ChannelPrivateError, UsernameInvalidError,\
    UsernameNotOccupiedError
from telegram.ext import DelayQueue
from utils import filter_emojis, init_settings, stringify_group_entity,\
    dedupe_members_and_merge

str_ftime_str = '%d-%m-%Y@%H:%M:%S'
logging_level = logging.INFO
settings_file_path = 'settings.json'
data_path = 'data'

logging.basicConfig(
    level=logging_level,
    format='%(asctime)s| %(message)s'
)
logging.getLogger('telethon').setLevel(level=logging.INFO)
logger = logging.getLogger()


async def process_group(group_entity):
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

    # If it is a channel we get the attached group chat
    try:
        chat = group_full.chats[1] \
                if group_full.chats[0].broadcast else group_full.chats[0]
    except IndexError:
        logger.warning(
            f'{group_entity} is a channel without a discussion group, skipped'
        )
        return 0

    target_group_dict = {
        'last_update': datetime.now(),
        'id': chat.id,
        'access_hash': chat.access_hash,
        'title': filter_emojis(chat.title),
        'tags': [],
        'members': []
    }
    try:
        target_group_dict['tags'] = group_entity['tags']
    except (KeyError, TypeError):
        pass

    try:
        with open(f'{data_path}/{target_group_dict["id"]}.json', 'r') as\
                target_group_file:
            target_group_dict['members'] = \
                json.load(target_group_file)['members']
    except FileNotFoundError:
        pass

    # Must be done twice because aggressive doesn't get users with
    # non latin names, and normal one doesn't get all users
    participants_non_aggressive = await client.get_participants(
        chat,
    )
    participants_non_aggressive = [*map(
        lambda x: {
            'id': x.id,
            'access_hash': x.access_hash,
            'first_name': filter_emojis(x.first_name),
            'last_name': filter_emojis(x.last_name),
            'username': x.username,
            'phone': x.phone
        },
        filter(
            lambda x: x.id not in settings['user_exceptions'] and not x.bot,
            participants_non_aggressive
        )
    )]

    participants = await client.get_participants(
        chat,
        aggressive=True
    )

    participants = [*map(
        lambda x: {
            'id': x.id,
            'access_hash': x.access_hash,
            'first_name': filter_emojis(x.first_name),
            'last_name': filter_emojis(x.last_name),
            'username': x.username,
            'phone': x.phone
        },
        filter(
            lambda x: x.id not in settings['user_exceptions'] and not x.bot,
            participants
        )
    )]

    participants = dedupe_members_and_merge(
        participants, participants_non_aggressive
    )

    target_group_dict['members'] = dedupe_members_and_merge(
        target_group_dict['members'], participants
    )

    with open(f'{data_path}/{target_group_dict["id"]}.json', 'w') as\
            target_group_file:
        json.dump(target_group_dict, target_group_file, indent=4,
                  default=str, ensure_ascii=False)

    logger.info('Data successfully collected from'
                f' {target_group_dict["title"]}'
                f'({target_group_dict["id"]})')
    return len(participants)


async def main(settings, client):
    total_users_scraped = 0
    total_groups_scraped = 0
    start_time = datetime.now()

    current_user = await client.get_me()
    settings['user_exceptions'].append(current_user.id)

    for group_entity in settings['target_groups']:
        try:
            number_of_users = await process_group(group_entity)
            total_users_scraped += number_of_users
            total_groups_scraped += 1
        except (
            ChannelPrivateError,
            UsernameInvalidError,
            UsernameNotOccupiedError,
            ValueError
        ) as e:
            logger.error(
                f"{stringify_group_entity(group_entity)}: {e}"
            )
            continue

    time_delta = datetime.now() - start_time
    logger.info('Statistics')
    logger.info(f'Total users scraped: {total_users_scraped}')
    logger.info(f'Total groups scraped: {total_groups_scraped}')
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
