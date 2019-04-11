import datetime, os, src.utils.twutils as twutils
from enum import Enum
from instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError

from config import LAST_FILE_PATH

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

def get_feed():
    last = read_last()
    highest = last

    web_api = Client(auto_patch=True, drop_incompat_keys=False)
    user_feed = web_api.user_feed(os.getenv('INSTAGRAM_USERID'), count=23)

    #data_file = open('data.txt', 'w+', encoding='utf-8')
    for post in reversed(user_feed):
        #data_file.write(str(post) + '\n')

        # ID comes in the format 'POSTID_USERID'
        post_id = int(post['node']['id'].split('_')[0])

        # If has not been processed already
        if post_id > last:
            # Hashtag
            tweet_metadata = ['#鈴木このみ', ' ']

            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp'])
            tweet_metadata += [timestamp.strftime('%Y-%m-%d %H:%M'), '\n']

            # Post URL
            tweet_metadata.append(post['node']['link'])

            # Caption
            caption = post['node']['caption']['text']
            tweet_content = ['\n\n', caption]

            media = [] # List of tuples of (type, url)

            if post['node']['__typename'] == 'GraphSidecar':
                print('gallery')

            elif post['node']['__typename'] == 'GraphVideo':
                media.append([post['node']['video_url']])

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
                api = open('result', 'a', encoding='utf-8')

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
            if post_id > highest:
                highest = post_id

        # if (highest > last):
        #     last = highest
        #     last_file = open(LAST_FILE_PATH, 'w', encoding='utf-8')
        #     last_file.write(str(last))
        #     last_file.close()