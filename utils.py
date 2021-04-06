import re
import json
import sys
import logging


def filter_emojis(text):
    pattern = "["\
            "\U0001F600-\U0001F64F"\
            "\U0001F300-\U0001F5FF"\
            "\U0001F680-\U0001F6FF"\
            "\U0001F1E0-\U0001F1FF"\
            "\U00002500-\U00002BEF"\
            "\U00002702-\U000027B0"\
            "\U00002702-\U000027B0"\
            "\U000024C2-\U0001F251"\
            "\U0001f926-\U0001f937"\
            "\U00010000-\U0010ffff"\
            "\u2640-\u2642"\
            "\u2600-\u2B55"\
            "\u200d"\
            "\u23cf"\
            "\u23e9"\
            "\u231a"\
            "\ufe0f"\
            "\u3030"\
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
        return f'{group_entity["title"]}'
    else:
        return f"{group_entity}"

