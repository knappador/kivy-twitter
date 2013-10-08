from kivy.app import App
from kivy.logger import Logger
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.uix.stacklayout import StackLayout
from kivy.uix.relativelayout import RelativeLayout

from twitter import Twitter
import netcheck


class ModalCtl:
    ''' just a container for keeping track of modals'''
    pass

class AskUser(RelativeLayout):
    ''' Callback(bool) if user wants to do something'''
    action_name = StringProperty()
    cancel_name = StringProperty()
    text = StringProperty()
    
    def __init__(self, 
                 action_name='Okay', 
                 cancel_name='Cancel', 
                 text='Are you Sure?',
                 callback=None, # Why would you do this?
                 *args, **kwargs):
        self.action_name = action_name
        self.cancel_name = cancel_name
        self._callback = callback
        self.text = text
        modal_ctl.modal = self
        super(AskUser, self).__init__(*args, **kwargs)

    def answer(self, yesno):
        ''' Callbacks in prompts that open prompts lead to errant clicks'''
        modal_ctl.modal.dismiss()
        if self._callback:
            def delay_me(*args):
                self._callback(yesno)
            Clock.schedule_once(delay_me, 0.1)


class TweetButton(Button):
    def on_press(self):
        def print_request(success, msg):
            if success:
                Logger.info('Application notified that tweet succeeded')
            else:
                Logger.info('Application notified that tweet failed')
        app.twitter.tweet(app.ttext.text, print_request)


class TweetImageButton(Button):
    def on_press(self):
        def print_request(success, msg):
            if success:
                Logger.info('Application notified that tweet succeeded')
            else:
                Logger.info('Application notified that tweet failed')
        app.twitter.tweet_photo(app.ttext.text, 
                                './images/kaleidoscope-thumb.jpg',
                                print_request)


class TwitterApp(App):
    def __init__(self, *args, **kwargs):
        global app
        app = self
        global modal_ctl
        modal_ctl = ModalCtl()
        super(TwitterApp, self).__init__(*args, **kwargs)

    def on_start(self):
        netcheck.set_prompt(self.ask_connect)
        creds = {'consumer_key' : '4N5RNkH9Zkm3qtxbYbi6Fg',
                 'consumer_secret' : 'YjyTa1hHExzWSVQqkuR4JAK2yFPrgD3dDl6sjulg'}
        self.twitter = Twitter(creds)
        self.twitter.set_retry_prompt(self.ask_retry_tweet)


    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def build(self):
        self.ttext = TextInput(text='Kivy will set you free!',
                                 size_hint=(1.0, 0.3),
                                 font_size=18)
        tb = TweetButton(text='Tweet Text',
                         size_hint=(0.5, 0.2))
        tib = TweetImageButton(text='Tweet Photo',
                         size_hint=(0.5, 0.2))
        root = StackLayout()
        root.add_widget(self.ttext)
        root.add_widget(tb)
        root.add_widget(tib)
        return root

    def ask_connect(self, tried_connect_callback):
        Logger.info('Opening net connect prompt')
        text = ('You need internet access to do that.  Do you '
                'want to go to settings to try connecting?')
        content = AskUser(text=text,
                          action_name='Settings',
                          callback=tried_connect_callback,
                          auto_dismiss=False)
        p = Popup(title = 'Network Unavailable',
                  content = content,
                  size_hint=(0.8, 0.4),
                  pos_hint={'x':0.1, 'y': 0.35})
        modal_ctl.modal = p
        p.open()

    def ask_retry_tweet(self, retry_twitter_callback):
        Logger.info('Tweet Failed')
        text = ('There was a problem sending the tweet.  Would'
                ' you like to retry?')
        content = AskUser(text=text,
                          action_name='Retry',
                          callback=retry_twitter_callback,
                          auto_dismiss=False)
        p = Popup(title = 'Tweet Failed',
                  content = content,
                  size_hint=(0.8, 0.4),
                  pos_hint={'x':0.1, 'y': 0.35})
        modal_ctl.modal = p
        p.open()


if __name__ == '__main__':
    TwitterApp().run()
