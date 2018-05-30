import codecs, datetime, json, math, os, requests, twitter
from bs4 import BeautifulSoup
from dotenv import load_dotenv

prof_url = 'https://www.instagram.com/{}/'
story_url = 'https://i.instagram.com/api/v1/feed/user/{}/reel_media/'
post_url = 'https://www.instagram.com/p/{}/'

def fetch_data(url):
    source = BeautifulSoup(requests.get(url).text, 'html.parser')
    script = source.find('script', text=lambda t: t.startswith('window._sharedData'))
    json_data = script.text.split(' = ', 1)[1].rstrip(';')
    return json.loads(json_data)

def check_length(tweet_str):
    if twitter.twitter_utils.calc_expected_status_length(tweet_str) > 280:
        return tweet_str[:278] + '…'
    else:
        return tweet_str

def main():
    # Load .env file variables
    load_dotenv()

    # Read in last parsed post ID
    last_str = codecs.open('last', 'r', 'utf-8').read()
    try:
        last = int(last_str)
    except ValueError:
        last = 0

    highest = last

    # Get user data
    post_data = fetch_data(prof_url.format(os.getenv("INSTAGRAM_USERNAME")))['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']

    # Loop through data
    for post in reversed(post_data):
        id = int(post['node']['id'])

        # If has not been processed already
        if id > last:
            # Hashtag
            tweet_metadata = [os.getenv("TWITTER_HASHTAG"), ' ']

            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp'])
            tweet_metadata += [timestamp.strftime('%Y-%m-%d %H:%M'), '\n']

            # Format post URL
            url = post_url.format(post['node']['shortcode'])
            tweet_metadata += [url, '\n\n']

            # Caption
            caption = post['node']['edge_media_to_caption']['edges'][0]['node']['text']
            tweet_content = [caption]

            images = []
            # If contains multiple images, get all images
            if post['node']['__typename'] == 'GraphSidecar':
                gallery_data = fetch_data(url)['entry_data']['PostPage'][0]['graphql']['shortcode_media']['edge_sidecar_to_children']['edges']
                for image in gallery_data:
                    images.append(image['node']['display_url'])
            else:
                images.append(post['node']['display_url'])

            tweet_str = check_length(''.join(tweet_metadata + tweet_content))

            # Authenticate with Twitter
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
                prev_status = api.PostUpdate(tweet_str, tweet_images, in_reply_to_status_id=prev_status).id

            # Update highest ID if higher
            if id > highest:
                highest = id
        else:
            break

    if (highest > last):
        last = highest
        file = codecs.open('last', 'w', 'utf-8')
        file.write(str(last))

if __name__ == "__main__":
    main()