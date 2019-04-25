import codecs, json, os
from instagram_private_api import Client, ClientCompatPatch, ClientError, ClientLoginError, ClientCookieExpiredError, ClientLoginRequiredError, ClientCheckpointRequiredError, ClientChallengeRequiredError

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

def get_client():
    USERNAME = os.getenv('INSTAGRAM_USERNAME')
    PASSWORD = os.getenv('INSTAGRAM_PASSWORD')

    try:
        if not os.path.isfile(SETTINGS_FILE_PATH):
            insta_api = Client(USERNAME, PASSWORD, on_login=lambda x: login_callback(x, SETTINGS_FILE_PATH))
        else:
            with open(SETTINGS_FILE_PATH) as settings_file:
                cached_settings = json.load(settings_file, object_hook=from_json)
            print('Reusing settings: {0!s}'.format(SETTINGS_FILE_PATH))

            insta_api = Client(USERNAME, PASSWORD, settings=cached_settings)

    except ClientCheckpointRequiredError as e:
        print('Exception: {0!s}'.format(e))
        exit(-1)
    except ClientChallengeRequiredError as e:
        print('Exception: {0!s}'.format(e))
        exit(-1)
    except (ClientCookieExpiredError, ClientLoginRequiredError) as e:
        print('Exception: {0!s}'.format(e))
        exit(-1)
    except Exception as e:
        print('Exception: {0!s}'.format(e))
        exit(-1)

    return insta_api