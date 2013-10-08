from kivy import platform

__all__ = ('open_url')

if platform() == 'android': 
    from androidbrowser import open_url
else:
    from mockbrowser import open_url
