from kivy.logger import Logger
from kivy.app import App

from jnius import autoclass, cast
from android import activity

Logger.info('Importing Android connection check')

activity = autoclass('org.renpy.android.PythonActivity').mActivity
Context = autoclass('android.content.Context') # cannot access this string on context?
ConnectivityManager = autoclass('android.net.ConnectivityManager')
Settings = autoclass('android.provider.Settings')
Intent = autoclass('android.content.Intent')
        
class Netcheck():
    def __init__(self, prompt=None):
        if prompt is None:
            prompt = self._no_prompt
        self._prompt = prompt
    
    def set_prompt(self, fn):
        self._prompt = fn
    
    def connection_available(self):
        cm = activity.getSystemService(Context.CONNECTIVITY_SERVICE)
        if cm is not None:
            info = cm.getActiveNetworkInfo()
            if info is not None:
                connected = info.isConnectedOrConnecting()
                Logger.debug('Connected or connecting: {}'.format(connected))
                return connected
        return False

    def ask_connect(self, callback=None):
        callback = callback if callback else lambda *args, **kwargs: None
        if self.connection_available():
            callback(True)
        else:
            self._callback = callback
            self._prompt(self._open_settings)

    def _open_settings(self, try_connect):
        if try_connect:
            app = App.get_running_app()
            app.bind(on_resume=self._settings_callback)
            activity.startActivityForResult(
                Intent(Settings.ACTION_WIRELESS_SETTINGS), 0)
        else:
            self._callback(False)
        
    def _settings_callback(self, *args):
        app = App.get_running_app()
        app.unbind(on_resume=self._settings_callback)        
        self._callback(self.connection_available())

    def _no_prompt(self, callback):
        Logger.warning('No network prompt was set.  Cannot ask to connect')
