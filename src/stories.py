import datetime, codecs, json, os, src.last, pytz
from instagram_private_api import Client, ClientCompatPatch, ClientError, ClientLoginError, ClientCookieExpiredError, ClientLoginRequiredError

from config import SETTINGS_FILE_PATH

def to_json(python_object):
    if isinstance(python_object, bytes):
        return {'__class__': 'bytes',
                '__value__': codecs.encode(python_object, 'base64').decode()}
    raise TypeError(repr(python_object) + ' is not JSON serializable')

def from_json(json_object):
    if '__class__' in json_object and json_object['__class__'] == 'bytes':
        return codecs.decode(json_object['__value__'].encode(), 'base64')
    return json_object

def login_callback(api, settings_file):
    cache_settings = api.settings
    with open(settings_file, 'w') as outfile:
        json.dump(cache_settings, outfile, default=to_json)
        print('Saved: {0!s}'.format(settings_file))

USERNAME = 'konjames142'
PASSWORD = '6fi7%e4D#$^m2W!fEmRh'

def get_stories(twitter_api):
    last = src.last.get_last(src.last.PostType.STORY)
    highest = last

    try:
        if not os.path.isfile(SETTINGS_FILE_PATH):
            insta_api = Client(USERNAME, PASSWORD, on_login=lambda x: login_callback(x, SETTINGS_FILE_PATH))
        else:
            with open(SETTINGS_FILE_PATH) as settings_file:
                cached_settings = json.load(settings_file, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(SETTINGS_FILE_PATH))

            insta_api = Client(USERNAME, PASSWORD, settings=cached_settings)

    #except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
    except Exception as e:
        print('Exception: {0!s}'.format(e))
        exit(-1)

    # Show when login expires
    cookie_expiry = insta_api.cookie_jar.auth_expires
    print('Cookie Expiry: {0!s}'.format(datetime.datetime.fromtimestamp(cookie_expiry).strftime('%Y-%m-%dT%H:%M:%SZ')))

    data = insta_api.user_story_feed(os.getenv('INSTAGRAM_USERID'))

    if data['reel'] != None:
        for item in data['reel']['items']:
            story_id = item['pk']
            if (story_id > last):
                print(story_id)
                print(item['taken_at'])
                timestamp = datetime.datetime.fromtimestamp(item['taken_at'], pytz.timezone('Asia/Tokyo'))
                tweet_data = ['【Story】 #鈴木このみ ', timestamp.strftime('%Y-%m-%d %H:%M')]
                if os.getenv('ENV', 'dev') == 'production':
                    twitter_api.PostUpdate(''.join(tweet_data), item['video_versions'][0]['url'])
                else:
                    twitter_api.write(''.join(tweet_data) + '\n\n')
                    twitter_api.write(item['video_versions'][0]['url'] + '\n\n')

                if story_id > highest:
                    highest = story_id
        
        if highest > last:
            src.last.set_last(str(highest), src.last.PostType.STORY)
