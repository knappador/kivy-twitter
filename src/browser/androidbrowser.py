from jnius import autoclass, cast

context = autoclass('org.renpy.android.PythonActivity').mActivity    
Uri = autoclass('android.net.Uri')
Intent = autoclass('android.content.Intent')

def open_url(url):
    ''' Open a webpage in the default Android browser.  '''
    intent = Intent()
    intent.setAction(Intent.ACTION_VIEW)
    intent.setData(Uri.parse(url))
    currentActivity = cast('android.app.Activity', context)
    currentActivity.startActivity(intent)
