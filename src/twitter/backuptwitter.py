from kivy import platform
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, StringProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

if platform() == 'android':
    from jnius import autoclass, PythonJavaClass, java_method, cast
    from android import activity
    from android.runnable import run_on_ui_thread

    context = autoclass('org.renpy.android.PythonActivity').mActivity    
    cb = autoclass('twitter4j.conf.ConfigurationBuilder')
    TwitterFactory = autoclass('twitter4j.TwitterFactory')        
    
class Twitter(EventDispatcher):
    ready = BooleanProperty(False)
    def __init__(self):
        self.open_connection()
        self.requests = list()

    def open_connection(self):
        self.ready = True

    def tweet(self, message, callback):
        #self.requests.append
        #Clock.schedule_once(self.dummy_callback, 0.05)
        print message
        callback('posted')

    #def dummy_callback(self, *args):
    #    r = self.requests.pop()[0]()
        


if platform() == 'android':
    Logger.info('Using Android Twitter class')



    class AndroidTwitter(Twitter):
        def __init__(self, *args, **kwargs):
            super(AndroidTwitter, self).__init__(*args, **kwargs)
            self.conf = cb()
            self.conf.setDebugEnabled(True)
            self.conf.setOAuthConsumerKey('5hTVgx1ptFrriQL2PaN8g')
            self.conf.setOAuthConsumerSecret('5bMd0xmH5RbQZu2BhYM2i9TuATdah9IW0aWhlKOg')
            self.conf.setOAuthAccessToken('1713735584-hCBNBHrK3mubnf2kCABYsZQztLuQ6SKarb8eyLe')
            self.conf.setOAuthAccessTokenSecret('JrnkbziRyy13bxAebsdKACoqoti23ru71SDOe4kWvU')
            tf = TwitterFactory(self.conf.build())
            self.twitter = tf.getInstance()

        def tweet(self, tweet, callback):
            self.twitter.updateStatus(tweet)
            callback('posted')


else:
    class AndroidTwitter(Twitter):
        pass




'''

package twitter4j.examples.async;

import twitter4j.*;



/**
 * <p>This is a code example of Twitter4J async API.<br>
 * Usage: java twitter4j.examples.AsyncUpdate <i>TwitterID</i> <i>TwitterPassword</i> <i>text</i><br>
 * </p>
 *
 * @author Yusuke Yamamoto - yusuke at mac.com
 */
public final class AsyncUpdate {
    /**
     * Main entry for this application.
     *
     * @param args String[] TwitterID TwitterPassword StatusString
     * @throws InterruptedException
     */

    static final Object LOCK = new Object();

    public static void main(String[] args) throws InterruptedException {
        if (args.length < 1) {
            System.out.println("Usage: java twitter4j.examples.AsyncUpdate text");
            System.exit(-1);
        }
        AsyncTwitterFactory factory = new AsyncTwitterFactory();
        AsyncTwitter twitter = factory.getInstance();
        twitter.addListener(new TwitterAdapter() {
            @Override
            public void updatedStatus(Status status) {
                System.out.println("Successfully updated the status to [" +
                        status.getText() + "].");
                synchronized (LOCK) {
                    LOCK.notify();
                }
            }

            @Override
            public void onException(TwitterException e, TwitterMethod method) {
                if (method == UPDATE_STATUS) {
                    e.printStackTrace();
                    synchronized (LOCK) {
                        LOCK.notify();
                    }
                } else {
                    synchronized (LOCK) {
                        LOCK.notify();
                    }
                    throw new AssertionError("Should not happen");
                }
            }
        });
        twitter.updateStatus(args[0]);
        synchronized (LOCK) {
            LOCK.wait();
        }
    }

}'''
