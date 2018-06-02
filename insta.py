# coding: utf-8

import datetime, json, math, os, requests, twitter, src.twutils as twutils
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from enum import Enum

LAST_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'last')
PROFILE_URL = 'https://www.instagram.com/{}/'
STORY_URL = 'https://i.instagram.com/api/v1/feed/user/{}/reel_media/'
POST_URL = 'https://www.instagram.com/p/{}/'

class PageType(Enum):
    PROFILE = 'ProfilePage'
    POST = 'PostPage'

class MediaType(Enum):
    IMAGE = 'GraphImage'
    VIDEO = 'GraphVideo'
    GALLERY = 'GraphSidecar'

def read_last():
    try:
        last_file = open(LAST_FILE_PATH, 'r', encoding='utf-8')
    except FileNotFoundError:
        last_file = open(LAST_FILE_PATH, 'w+', encoding='utf-8')
    last_str = last_file.read()
    last_file.close()
    try:
        return int(last_str)
    except ValueError:
        return 0

def download_json_data(url):
    source = BeautifulSoup(requests.get(url).text, 'html.parser')
    script = source.find('script', text=lambda t: t.startswith('window._sharedData'))
    json_data = script.text.split(' = ', 1)[1].rstrip(';')
    return json.loads(json_data)

def get_data(url, type=PageType.POST, media_type=MediaType.IMAGE):
    json_data = download_json_data(url)
    if type == PageType.PROFILE:
        return json_data['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
    else:
        if media_type == MediaType.GALLERY:
            return json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
        elif media_type == MediaType.VIDEO:
            return json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['video_url']
        else:
            return json_data['entry_data']['PostPage'][0]['graphql']['shortcode_media']['display_url']

def main():
    # Load .env file variables
    load_dotenv()

    # Read in last parsed post ID
    last = read_last()
    highest = last

    # Get user data
    profile_data = get_data(PROFILE_URL.format(os.getenv("INSTAGRAM_USERNAME")), PageType.PROFILE)
    
    # Loop through data
    for post in reversed(profile_data):
        id = int(post['node']['id'])

        # If has not been processed already
        if id > last:
            # Hashtag
            tweet_metadata = ['#鈴木このみ', ' ']

            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp'])
            tweet_metadata += [timestamp.strftime('%Y-%m-%d %H:%M'), '\n']

            # Format post URL
            url = POST_URL.format(post['node']['shortcode'])
            tweet_metadata.append(url)

            # Caption
            caption = post['node']['edge_media_to_caption']['edges'][0]['node']['text']
            tweet_content = ['\n\n', caption]

            images = []
            media = [] # List of tuples of (type, url)
            # If gallery, get all media
            if post['node']['__typename'] == MediaType.GALLERY.value:
                list_idx = 0
                list_type = None
                media_list = []
                gallery_data = get_data(url, media_type=MediaType.GALLERY)
                for gallery_item in gallery_data:
                    if gallery_item['node']['__typename'] == MediaType.VIDEO.value:
                        if list_type is None:
                            media.append([gallery_item['node']['video_url']])
                        elif list_type is MediaType.IMAGE:
                            # Image list in progress
                            # Commit current list and create new list with video
                            media.append(media_list)
                            media.append([gallery_item['node']['video_url']])
                            list_type = None
                            media_list = []
                    else:
                        if list_type is None:
                            # No list in progress
                            list_type = MediaType.IMAGE
                            media_list.append(gallery_item['node']['display_url'])
                        elif list_type is MediaType.IMAGE:
                            # Image list in progress
                            if len(media_list) > 4:
                                # List is somehow overfull
                                # Tweets only allow 4 images, so extra ones need to be split
                                while len(media_list) >= 4:
                                    media.append(media_list[:4])
                                    media_list = media_list[4:]
                                media_list.append(gallery_item['node']['display_url'])
                            elif len(media_list) == 4:
                                # List full
                                # Commit current list and create new list
                                media.append(media_list)
                                media_list = [gallery_item['node']['display_url']]
                            else:
                                # List not full yet
                                media_list.append(gallery_item['node']['display_url'])
                # Commit unfinished list if exists
                if list_type is MediaType.IMAGE and len(media_list) > 0:
                    media.append(media_list)
            elif post['node']['__typename'] == MediaType.VIDEO.value:
                media.append([get_data(url, media_type=MediaType.VIDEO)])
            else:
                media.append([post['node']['display_url']])

            api = None
            # If production, authenticate with Twitter
            if os.getenv('ENV', 'dev') == 'production':
                api = twitter.Api(consumer_key=os.getenv("CONSUMER_KEY"),
                                consumer_secret=os.getenv("CONSUMER_SECRET"),
                                access_token_key=os.getenv("ACCESS_TOKEN_KEY"),
                                access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"))
            else:
                api = open('result', 'w', encoding='utf-8')

            tweet_str = twutils.truncate_status(''.join(tweet_metadata + tweet_content))

            prev_status = 0
            for tweet_media in media:
                replyto = None
                if (prev_status > 0):
                    tweet_str = twutils.truncate_status(''.join(tweet_metadata))
                    replyto = prev_status

                if os.getenv('ENV', 'dev') == 'production':
                    prev_status = api.PostUpdate(tweet_str, tweet_media, in_reply_to_status_id=prev_status).id
                else:
                    prev_status += 1
                    api.write(tweet_str + '\n\n')
                    api.write('\n'.join(tweet_media) + '\n\n')

            # Update highest ID if higher
            if id > highest:
                highest = id

    if (highest > last):
        last = highest
        last_file = open(LAST_FILE_PATH, 'w', encoding='utf-8')
        last_file.write(str(last))
        last_file.close()

if __name__ == "__main__":
    main()