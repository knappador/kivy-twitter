''' This mock only logs and matches signatures.  Enjoy'''
from kivy.logger import Logger

def open_url(url):
    Logger.info('Browser: {}.  Would call startActivity(Intent)'.format(
        url))
