kivy-twitter
=============

Tweet your face off. Take a photo of your face, then tweet it!

#### Features
* oAuth workflow with pretty good UX and retry prompts
* saves credentials
* tweets
* photos
* uses toasts and netcheck to make UX better

#### Install
Pre-built application in ```/bin```
adb install -r /bin/TwitterExample-0.1-debug-unaligned.apk

#### Build With P4A
Copy the jar files in libs/ to your dist

If you want your own twitter applciation, go to: 
https://dev.twitter.com/
* Set a callback URL even though you don't have one.  Use kivy.org for all I care.
* Edit and insert AndroidManifest.extras.xml to your P4A templates/AndroidManifest.xml
* Edit the callback in src/twitter/androidtwitter.py called CALLBACK_URL
* Double check all of this as it's necessary for the browser to call your app back
* If you screw up the broswer will act like 404 or even open a different app when returning from twitter.

Copy the browser.sh to a P4A dist then run:
```twitter.sh my/path/to/app/```
If it doesn't work, edit twitter.sh to configure P4A to build this.  Need PyJNIus in your dist. 

#### Debuggable
```src/browser/main.py``` It does quite a few things to let you debug the UX

#### Docs
Public API.

Contact me for support
