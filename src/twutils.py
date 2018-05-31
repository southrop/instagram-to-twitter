# encoding: utf-8

import re
import twitter.twitter_utils as twitter_utils
from unicodedata import normalize

def truncate_status(status):
    if twitter_utils.calc_expected_status_length(status) <= 280:
        return status
    else:
        while twitter_utils.calc_expected_status_length(status) > 278:
            status = status[:len(status)-1]

        status += '…'
        return status
