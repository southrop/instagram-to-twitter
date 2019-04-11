import os
import src.feed
from dotenv import load_dotenv

def main():
    # Load .env file variables
    load_dotenv()

    src.feed.get_feed()

if __name__ == '__main__':
    main()
