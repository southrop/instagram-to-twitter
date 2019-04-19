import os, twitter
from src import feed, stories, last
from dotenv import load_dotenv

def main():
    # Load .env file variables
    load_dotenv()

    twitter_api = None
    # If production, authenticate with Twitter
    if os.getenv('ENV', 'dev') == 'production':
        twitter_api = twitter.Api(consumer_key=os.getenv("CONSUMER_KEY"),
                        consumer_secret=os.getenv("CONSUMER_SECRET"),
                        access_token_key=os.getenv("ACCESS_TOKEN_KEY"),
                        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"))
    else:
        twitter_api = open('result', 'a', encoding='utf-8')

    feed.get_feed(twitter_api)
    stories.get_stories(twitter_api)

if __name__ == '__main__':
    main()
