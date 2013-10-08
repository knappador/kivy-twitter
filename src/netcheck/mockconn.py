from kivy.logger import Logger

''' Mock for checking the connection.  Set success to test '''

class Netcheck():
    def __init__(self, prompt=None):
        if prompt is None:
            prompt = self._no_prompt
        self._prompt = prompt
        self.MOCK_RESULT=False
        self.MOCK_SETTINGS_RESULT=True
    
    def set_prompt(self, fn):
        self._prompt = fn
    
    def connection_available(self):
        Logger.info('Mock connection check {}'.format(self.MOCK_RESULT))
        return self.MOCK_RESULT

    def ask_connect(self, callback=None):
        callback = callback if callback else lambda *args, **kwargs: None
        if self.connection_available():
            callback(True)
        else:
            self._callback = callback
            self._prompt(self._open_settings)

    def _open_settings(self, try_connect):
        Logger.info('in ask connect callback ' + str(try_connect))
        if try_connect:
            self._settings_callback()
        else:
            self._callback(False)
        
    def _settings_callback(self):
        self.MOCK_RESULT=self.MOCK_SETTINGS_RESULT
        self._callback(self.MOCK_SETTINGS_RESULT)

    def _no_prompt(self, callback):
        Logger.warning('No network prompt was set.  Cannot ask to connect')

    def _set_debug(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])
