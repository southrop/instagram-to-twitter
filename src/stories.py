import datetime, os, pytz, src.auth, src.last
from instagram_private_api import Client, ClientCompatPatch, ClientError, ClientLoginError, ClientCookieExpiredError, ClientLoginRequiredError

def get_stories(twitter_api):
    last = src.last.get_last(src.last.PostType.STORY)
    highest = last

    insta_api = src.auth.get_client()

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
