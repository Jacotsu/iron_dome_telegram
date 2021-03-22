#!/usr/bin/env python3
import random
import logging
import json
import sys
from pathlib import Path


if __name__ == '__main__':
    hostile_dict = {}
    for path in sys.argv[1:-1]:
        with open(path, 'r') as group_of_hostiles_file:
            hostile_group = json.load(group_of_hostiles_file)
            for user in hostile_group['members']:
                # This removes duplicates
                hostile_dict[user['id']] = user

    with open(sys.argv[-1], 'r') as group_of_member_to_check_file:
        members_dict = {}
        group = json.load(group_of_member_to_check_file)
        for user in group['members']:
            # This removes duplicates
            members_dict[user['id']] = user

        hostile_set = set(hostile_dict)
        members_set = set(members_dict)

        for id in members_set.intersection(hostile_set):
            print(members_dict[id])
