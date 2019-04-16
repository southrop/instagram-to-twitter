import datetime, os, src.last, src.utils.twutils as twutils, pytz
from enum import Enum
from instagram_web_api import Client, ClientCompatPatch, ClientError, ClientLoginError

class MediaType(Enum):
    IMAGE = 'GraphImage'
    VIDEO = 'GraphVideo'
    GALLERY = 'GraphSidecar'

def get_feed(twitter_api):
    last = src.last.get_last(src.last.PostType.MEDIA)
    highest = last

    web_api = Client(auto_patch=True, drop_incompat_keys=False)
    user_feed = web_api.user_feed(os.getenv('INSTAGRAM_USERID'), count=23)

    for post in reversed(user_feed):
        # ID comes in the format 'POSTID_USERID'
        post_id = int(post['node']['id'].split('_')[0])

        # If has not been processed already
        if post_id > last:
            # Hashtag
            tweet_metadata = ['#鈴木このみ', ' ']

            # Format timestamp
            timestamp = datetime.datetime.fromtimestamp(post['node']['taken_at_timestamp'], pytz.timezone('Asia/Tokyo'))
            tweet_metadata += [timestamp.strftime('%Y-%m-%d %H:%M'), '\n']

            # Post URL
            tweet_metadata.append(post['node']['link'])

            # Caption
            caption = post['node']['caption']['text']
            tweet_content = ['\n\n', caption]

            media = [] # List of tuples of (type, url)

            if post['node']['__typename'] == MediaType.GALLERY.value:
                list_idx = 0
                list_type = None
                media_list = []
                for gallery_item in post['node']['edge_sidecar_to_children']['edges']:
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
                media.append([post['node']['video_url']])

            else:
                media.append([post['node']['display_url']])

            tweet_str = twutils.truncate_status(''.join(tweet_metadata + tweet_content))

            prev_status = 0
            for tweet_media in media:
                replyto = None
                if (prev_status > 0):
                    tweet_str = twutils.truncate_status(''.join(tweet_metadata))
                    replyto = prev_status

                if os.getenv('ENV', 'dev') == 'production':
                    prev_status = twitter_api.PostUpdate(tweet_str, tweet_media, in_reply_to_status_id=prev_status).id
                else:
                    prev_status += 1
                    twitter_api.write(tweet_str + '\n\n')
                    twitter_api.write('\n'.join(tweet_media) + '\n\n')

            # Update highest ID if higher
            if post_id > highest:
                highest = post_id

    if (highest > last):
        src.last.set_last(str(highest), src.last.PostType.MEDIA)