import datetime, json, math, os, requests, twitter
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

def check_length(tweet_str):
    if twitter.twitter_utils.calc_expected_status_length(tweet_str) > 280:
        return tweet_str[:278] + '…'
    else:
        return tweet_str

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
            tweet_metadata = [os.getenv("TWITTER_HASHTAG"), ' ']

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
            # If contains multiple images, get all images
            if post['node']['__typename'] == MediaType.GALLERY.value:
                gallery_data = get_data(url, media_type=MediaType.GALLERY)
                for image in gallery_data:
                    images.append(image['node']['display_url'])
            else:
                images.append(post['node']['display_url'])

            tweet_str = check_length(''.join(tweet_metadata + tweet_content))

            api = None
            # If production, authenticate with Twitter
            if os.getenv('ENV', 'dev') == 'production':
                api = twitter.Api(consumer_key=os.getenv("CONSUMER_KEY"),
                                consumer_secret=os.getenv("CONSUMER_SECRET"),
                                access_token_key=os.getenv("ACCESS_TOKEN_KEY"),
                                access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"))

            # Check number of tweets required
            tweets_required = math.ceil(len(images) / 4)
            prev_status = 0
            for i in range(tweets_required):
                start = i * 4
                tweet_images = images[start:start+4]
                replyto = None
                if (prev_status > 0):
                    tweet_str = check_length(''.join(tweet_metadata))
                    replyto = prev_status

                if os.getenv('ENV', 'dev') == 'production':
                    prev_status = api.PostUpdate(tweet_str, tweet_images, in_reply_to_status_id=prev_status).id

            # Update highest ID if higher
            if id > highest:
                highest = id

    if (highest > last):
        last = highest
        last_file = open(LAST_FILE_PATH, 'w', 'utf-8')
        last_file.write(str(last))
        last_file.close()

if __name__ == "__main__":
    main()