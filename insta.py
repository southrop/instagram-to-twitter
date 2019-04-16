import os
from src import feed, stories, last
from dotenv import load_dotenv

def main():
    # Load .env file variables
    load_dotenv()

    twitter = None
    # If production, authenticate with Twitter
    if os.getenv('ENV', 'dev') == 'production':
        api = twitter.Api(consumer_key=os.getenv("CONSUMER_KEY"),
                        consumer_secret=os.getenv("CONSUMER_SECRET"),
                        access_token_key=os.getenv("ACCESS_TOKEN_KEY"),
                        access_token_secret=os.getenv("ACCESS_TOKEN_SECRET"))
    else:
        twitter = open('result', 'a', encoding='utf-8')

    feed.get_feed(twitter)
    stories.get_stories(twitter)

if __name__ == '__main__':
    main()
