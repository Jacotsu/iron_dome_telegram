import re
import json
import sys
import logging
from copy import deepcopy


def filter_emojis(text):
    pattern = "["\
            "\u0000-\u0020"\
            "\u007F-\u00A0"\
            "\u2190-\u2BFE"\
            "\U0001F18B-\U0001F1AD"\
            "\U0001F200-\U0001FFFF"\
            "]+"
    if text:
        return re.sub(pattern, '', text, flags=re.UNICODE)
    else:
        return None


def init_settings(path):
    try:
        with open(path, 'r') as settings_file:
            settings = json.load(settings_file)
        return settings
    except FileNotFoundError:
        logging.error('Settings file not found, creating a new one')
        with open(path, 'w') as settings_file:
            json.dump(
                {
                    'api_id': None,
                    'api_hash': None,
                    'trigger_words': [],
                    'groups_to_preserve': [],
                    'user_exceptions': [],
                    'target_groups': []
                },
                settings_file,
                indent=4,
            )
        logging.error('Settings file created! please configure the program')
        sys.exit(0)


def stringify_user_dict(user):
    return f'{user["first_name"]} {user["last_name"]} {user["username"]}'\
            f'({user["id"]})'


def stringify_user(user):
    return f'{user.first_name} {user.last_name} {user.username}({user.id})'


def stringify_group_entity(group_entity):
    if isinstance(group_entity, dict):
        try:
            return f'{group_entity["title"]}'
        except KeyError:
            return f'{group_entity["group_id"]}'
    else:
        return f"{group_entity}"


def dedupe_members_and_merge(list_1, list_2):
    tmp = deepcopy(list_1)
    tmp_2 = deepcopy(list_2)
    for member_1 in list_1:
        for member_2 in list_2:
            if member_1['id'] == member_2['id']:
                try:
                    tmp_2.remove(member_2)
                except ValueError:
                    pass
                break
    tmp.extend(tmp_2)
    return tmp
