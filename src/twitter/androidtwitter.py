from kivy.logger import Logger
from kivy.app import App
from jnius import autoclass, PythonJavaClass, java_method, cast
from android import activity
#from android.runnable import run_on_ui_thread

# import urlparse  # foobar did not behave as expected, but easily done without
import netcheck
import toast
import browser
import os
import json
from functools import partial

context = autoclass('org.renpy.android.PythonActivity').mActivity    

# Python and Java VM GC's don't talk to each other
# save Python refs if Java might end up calling back to them
_refs = {}

#MMMMM java and callback verbosity for the asynchronous win
class _TwitterListener(PythonJavaClass):
    __javainterfaces__ = ['twitter4j.TwitterListener']
    __javacontext__ = 'app'

    def __init__(self, twitter):
        self.twitter = twitter
        super(_TwitterListener, self).__init__()

    @java_method('(Ltwitter4j/auth/RequestToken;)V')
    def gotOAuthRequestToken(self, request_token):
        creds = self.twitter.credentials
        creds['oauth_token'] = request_token.getToken()
        creds['oauth_token_secret'] = request_token.getTokenSecret()
        self.twitter._log_creds()
        self.twitter._awaiting_resume=True
        browser.open_url(request_token.getAuthorizationURL())

    @java_method('(Ltwitter4j/auth/AccessToken;)V')
    def gotOAuthAccessToken(self, access_token):
        creds = self.twitter.credentials
        creds['oauth_token'] = access_token.getToken()
        creds['oauth_token_secret'] = access_token.getTokenSecret()
        _refs['access_token'] = access_token
        self.twitter.tw.setOAuthAccessToken(access_token);
        self.twitter._log_creds()
        self.twitter._auth_state = 'authenticated'
        self.twitter._save_creds()
        self.twitter._process_request()

    @java_method('(Ltwitter4j/User;)V')
    def verifiedCredentials(self, user):
        Logger.info('Saved credentials were valid')
        self.twitter._auth_state = 'authenticated'
        self.twitter._process_request()
        
    @java_method('(Ltwitter4j/Status;)V')
    def updatedStatus(self, status):
        Logger.info('status update complete: {}'.format(status.getText()))
        self.twitter._success()
        
    @java_method('(Ltwitter4j/TwitterException;Ltwitter4j/TwitterMethod;)V')
    def onException(self, exception, method):
        msg = str(exception.getErrorMessage())
        Logger.error(msg)
        self.twitter._error_msg = msg
        self.twitter._tries -= 1
        self.twitter._run_async()


class Request():
    def __init__(self, payload, callback=None):
        self.payload = payload
        if callback is not None:
            self.callback = callback
        else:
            self.callback = lambda *args, **kwargs: None


# replace 'kivy' and 'twitter' if needed but keep consistent with
# but must be same as in AndroidManifest.xml
CALLBACK_URL= 'kivy://twitter'
MAX_ATTEMPTS = 3 # steps to try again on exception
SAVE_PATH = './twitter_credentials.json'
MAX_DIMENSION = 375 # for image tweets

class AndroidTwitter():
    ''' Twitter implementation that uses OAuth and Twitter API'''
    def __init__(self, credentials, toasty=True):
        self.credentials = credentials
        self._auth_state = None
        self._processing = False
        self._awaiting_resume=False
        self.toasty = toasty
        # bind to catch callback from browser
        activity.bind(on_new_intent=self._webview_intent_callback)
        App.get_running_app().bind(on_resume=self._check_resume)

    def tweet(self, status='test', callback=None):
        t = Request(payload=status, callback=callback)
        t.process = self._process_tweet
        # boolean True if request starts
        return self._new_request(t)

    def _process_tweet(self, tweet):
        Logger.info('Processing twitter tweet {}'.format(tweet.payload))
        self.tw.updateStatus(tweet.payload)

    def tweet_photo(self, status, path, callback=None, resize=True, jpeg=False):
        payload = {'status' : status,
                   'path' : path,
                   'resize' : resize,
                   'jpeg' : jpeg}
        t = Request(payload=payload, callback=callback)
        t.process = self._process_tweet_photo
        if not os.path.exists(t.payload['path']):
            callback(False, 'We couldn\'t find the file')
            return False
        return self._new_request(t)
        
    def _process_tweet_photo(self, tweet):
        payload = tweet.payload
        resize = payload['resize']
        jpeg = payload['jpeg']
        Logger.info('Processing twitter tweet {}'.format(payload['status']))
        if resize or jpeg:
            from PIL import Image
            photo = Image.open(payload['path'])
            photo.load()
        if resize:
            # lets resize the image to something manageable
            if photo.size[0] > MAX_DIMENSION or photo.size[1] > MAX_DIMENSION:
                if photo.size[0] > photo.size[1]:
                    width = MAX_DIMENSION
                    height = int(photo.size[1] * MAX_DIMENSION / photo.size[0])
                else:
                    height = MAX_DIMENSION
                    width = int(photo.size[0] * MAX_DIMENSION / photo.size[1])
                photo = photo.resize((width, height), Image.ANTIALIAS)
        if resize or jpeg:
            temp_base = './twitter_images/'
            if not os.path.exists(temp_base):
                os.makedirs(temp_base, 0700)
            tail = os.path.split(payload['path'])[1]
            if jpeg:
                tail = '.'.join(tail.split('.')[0:-1]) + '.jpg'
            temp_path = temp_base + tail
            with open(temp_path, 'w+') as f:
                if jpeg:
                    photo.save(f, format='JPEG', quality=85)
                else:
                    photo.save(f)
            payload['path'] = temp_path
        # ready to twitter4j that photo to mars as long as they have internet.
        StatusUpdate = autoclass('twitter4j.StatusUpdate')
        File = autoclass('java.io.File')
        status = StatusUpdate(payload['status'])
        imageFile = File(os.path.abspath(payload['path']))
        Logger.info(str(imageFile.getAbsolutePath()))
        status.setMedia(imageFile)
        self.tw.updateStatus(status)

    def _ask_retry(self):
        self.retry_prompt(self._fail_callback)

    def retry_prompt(self, callback):
        ''' monkey patch here to implement a real prompt'''
        callback(False)

    def set_retry_prompt(self, fn):
        self.retry_prompt = fn

    def _fail(self):
        self._toast('Tweet Failed')
        self._auth_state = None
        self._ask_retry()

    def _fail_callback(self, retry):
        if retry:
            self._tries = MAX_ATTEMPTS
            self._process_request()
        else:
            self._processing=False
            self._tries = 0
            self.request.callback(False, self._error_msg)
            self.request = None

    def _success(self):
        self._processing=False
        self._tries = 0
        self._toast('Successful Tweet!')
        self.request.callback(True, '')
        self.request = None
        
    def _new_request(self, request):
        self.request = request
        if not self._processing:
            self._tries = MAX_ATTEMPTS
            self._processing = True
            self._error_msg = 'There was a problem sending the tweet'
            self._process_request()
            self._toast('Connecting', False)
            return True
        self._toast('Tweet Already in Progress')
        return False

    def _connection_callback(self, connected):
        if connected:
            self._process_request()
        else:
            self._fail()

    def _process_request(self):
        if not self._tries > 0:
            self._fail()
        elif not netcheck.connection_available():
            netcheck.ask_connect(self._connection_callback)
        elif not self._auth_state == 'authenticated':
            self._authenticate()
        else:
            self._toast('Tweet Started')
            self._run_async(partial(self.request.process, self.request))

    def _authenticate(self):
        Logger.info('OAuth Implemented.  Launching OAuth workflow.')
        self._oauth_workflow()

    def _oauth_workflow(self):
        AsyncTwitterFactory = autoclass('twitter4j.AsyncTwitterFactory')
        self.tw = AsyncTwitterFactory().getSingleton()
        self._listener = _TwitterListener(self)
        self.tw.addListener(self._listener)
        self.tw.setOAuthConsumer(self.credentials['consumer_key'],
                                 self.credentials['consumer_secret'])
        if self._load_creds():
            # must check saved credentials
            AccessToken = autoclass('twitter4j.auth.AccessToken')
            access_token = AccessToken(self.credentials['oauth_token'],
                                       self.credentials['oauth_token_secret'])
            _refs['__at'] = access_token
            self.tw.setOAuthAccessToken(access_token)
            # will send us to _get_initial_tokens if 
            # _AsyncTwitter.verifiedCredentials fails
            self._async_step = self._get_initial_tokens
            self.tw.verifyCredentials()
        else:
            # let's get some tokens
            self._run_async(self._get_initial_tokens)

    def _get_initial_tokens(self):
        # results for async ops processed in listener
        # listener will retry if something f'd up
        requestToken = self.tw.getOAuthRequestTokenAsync(CALLBACK_URL)
            
    def _webview_intent_callback(self, intent):
        uri = intent.getData()
        # if the intent was for twitter, the CALLBACK_URL will match
        # Logger.info(str(uri.toString()))
        if (uri != None and uri.toString().startswith(CALLBACK_URL)):
            self._awaiting_resume=False
            try:
                s = uri.toString()
                Logger.info('got a twitter intent with uri: {}'.format(s))
                # urlparse seemed to screw up here.  oh well.  munge munge.
                result = dict((k, v) for k, v in map(lambda s: s.split('='), 
                                                     s.split('?')[-1].split('&')))
                self.credentials['oauth_verifier'] = result['oauth_verifier']
                self._run_async(self._get_final_tokens)
            except:
                self._tries -= 1
                # this will jump back to _get_initial_tokens
                self._run_async()
            return True
    
    def _check_resume(self, *args):
        if self._awaiting_resume:
            clock.schedule_once(self._check_fail(1.0))

    def _check_fail(self, dt):
        # if we haven't processed an intent after 1 second,
        # fail the tweet because the handler should have been called
        if self._awaiting_resume:
            self._fail()
        self._awaiting_resume=False
            
    def _get_final_tokens(self):
        RequestToken = autoclass('twitter4j.auth.RequestToken')
        request_token = RequestToken(self.credentials['oauth_token'],
                                     self.credentials['oauth_token_secret'])
        _refs['request_token'] = request_token
        self.tw.getOAuthAccessTokenAsync(request_token,
                                         self.credentials['oauth_verifier'])

    def _run_async(self, fn=None):
        if fn is not None:
            self._async_step = fn
        else:
            fn = self._async_step
        if self._tries > 0:
            if hasattr(fn, '__name__'):
                name = fn.__name__
            elif type(fn) == partial:
                name = fn.func.__name__
            else:
                name = str(fn)
            Logger.info('Running async step: {}'.format(name))
            fn()
        else:
            self._fail()        
            
    def _log_creds(self):
        Logger.info(str(self.credentials))

    def _save_creds(self):
        with open(SAVE_PATH, 'w+') as f:
            json.dump(self.credentials, f)

    def _load_creds(self):
        if os.path.exists(SAVE_PATH):
            with open(SAVE_PATH, 'r') as f:
                self.credentials.update(json.load(f))
            if 'oauth_token' in self.credentials and \
               'oauth_token_secret' in self.credentials:
                return True
        return False

    def _toast(self, text, length_long=False):
        if self.toasty:
            toast.toast(text, length_long)
