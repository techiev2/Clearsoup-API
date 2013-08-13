from user.handlers import UserHandler

URLS = [('/api/user/(?P<username>.*?)/?$', UserHandler),
       ]

__all__ = ['URLS']
