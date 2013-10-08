from kivy.logger import Logger
from kivy.clock import Clock

import netcheck

class Request():
    def __init__(self, payload, callback=None):
        self.payload = payload
        if callback is not None:
            self.callback = callback
        else:
            self.callback = lambda *args, **kwargs: None

MAX_ATTEMPTS=2

class MockTwitter():
    def __init__(self, credentials, toasty=True):
        self.credentials = credentials
        self._auth_state = None
        self._error_msg = 'OMg omg testin'
    
    def tweet(self, status='test', callback=None):
        t = Request(payload=status, callback=callback)
        t.process = self._process_tweet
        self.request = t
        self._process_request()

    def tweet_photo(self, status, path, callback=None, resize=True, jpeg=False):
        t = Request(payload=status, callback=callback)
        t.process = self._process_tweet
        self.request = t
        self._process_request()

    def _process_tweet(self, tweet):
        Logger.info('Tweeting {}'.format(tweet.payload))
        def fake_response(dt):
            Logger.info('in tweet callback')
            tweet.callback(True, 'Tweet was successful')
        Clock.schedule_once(fake_response, 0.5)

    def _process_request(self):
        if not netcheck.connection_available():
            netcheck.ask_connect(self._connection_callback)
        elif not self._auth_state == 'authenticated':
            self._authenticate()
        else:
            self.request.process(self.request)

    def _connection_callback(self, connected):
        Logger.info('in twitter connection callback: ' + str(connected))
        if connected:
            self._process_request()
        else:
            self._fail()

    def _authenticate(self):
        self._auth_state = 'authenticated'
        self._process_request()

    def _ask_retry(self):
        self.retry_prompt(self._fail_callback)

    def retry_prompt(self, callback):
        ''' monkey patch here to implement a real prompt'''
        callback(False)

    def set_retry_prompt(self, fn):
        self.retry_prompt = fn

    def _fail(self):
        self._auth_state = None
        self._ask_retry()

    def _fail_callback(self, retry):
        Logger.info('in fail callback ' + str(retry))
        if retry:
            self._tries = MAX_ATTEMPTS
            self._process_request()
        else:
            self._processing=False
            self._tries = 0
            self.request.callback(False, self._error_msg)
            self.request = None
