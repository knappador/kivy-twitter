from kivy import platform

__all__ = ('connection_available', 'set_retry_prompt', 'ask_connect', 
           '_get_ref')

_Netcheck = None

def _netcheck():
    global _Netcheck
    if _Netcheck is None:
        p = platform()
        if p == 'android': 
            from androidconn import Netcheck
        else:
            from mockconn import Netcheck
        _Netcheck = Netcheck()
    return _Netcheck

def connection_available():
    return (_netcheck().connection_available())

def set_prompt(fn):
    _netcheck().set_prompt(fn)

def ask_connect(callback):
    _netcheck().ask_connect(callback)

def _get_ref():
    return _netcheck()
