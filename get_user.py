#!/usr/bin/env python3
import logging
import sys
import json
from time import sleep
from telethon.sync import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from utils import filter_emojis, init_settings


logging_level = logging.INFO
settings_file_path = 'settings.json'
# 1 request per second
requests_wait_time = 1

logging.basicConfig(
    level=logging_level,
    format='%(asctime)s| %(message)s'
)
logging.getLogger('telethon').setLevel(level=logging.INFO)
logger = logging.getLogger()


if __name__ == '__main__':
    settings = init_settings(settings_file_path)
    logger.debug(f'Settings loaded: {settings}')

    with TelegramClient('iron_dome', settings['api_id'],
                        settings['api_hash']) as client:

        for username in sys.argv[1:]:
            full_user = client(GetFullUserRequest(username))
            print(json.dumps({
                'id': full_user.user.id,
                'access_hash': full_user.user.access_hash,
                'first_name': filter_emojis(full_user.user.first_name),
                'last_name': filter_emojis(full_user.user.last_name),
                'username': full_user.user.username,
                'phone': full_user.user.phone,
                'about': full_user.about,
                'status': str(full_user.user.status),
                'restricted': full_user.user.restricted,
                'restriction_reason': full_user.user.restriction_reason,
                'scam': full_user.user.scam
            }, indent=4))
            sleep(requests_wait_time)


