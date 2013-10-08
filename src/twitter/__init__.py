from kivy import platform

''' using init to handle conditional import '''

__all__ = ('Twitter')


p = platform()
if p == 'android':
    from androidtwitter import AndroidTwitter
    Twitter = AndroidTwitter
elif p == 'linux':
    from mocktwitter import MockTwitter
    Twitter = MockTwitter
