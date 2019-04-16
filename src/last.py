import json, os
from enum import Enum

from config import LAST_FILE_PATH

class PostType(Enum):
    MEDIA = 'Media'
    STORY = 'Story'

def read_last():
    if not os.path.isfile(LAST_FILE_PATH):
        return { 'media': '0', 'story': '0' }

    with open(LAST_FILE_PATH, 'r+') as last_file:
        return json.load(last_file)

def get_last(type=PostType.MEDIA):
    last_data = read_last()

    if type == PostType.STORY:
        last_str = last_data['story']
    elif type == PostType.MEDIA:
        last_str = last_data['media']

    try:
        return int(last_str)
    except ValueError:
        return 0

def set_last(value, type=PostType.MEDIA):
    last_data = read_last()

    if type == PostType.STORY:
        last_data['story'] = value
    elif type == PostType.MEDIA:
        last_data['media'] = value

    with open(LAST_FILE_PATH, 'w') as outfile:
        json.dump(last_data, outfile)