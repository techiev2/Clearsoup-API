from auth.handlers import Authenticate, Logout

URLS = [('/api/authenticate\/?$', Authenticate),
        ('/api/logout\/?$', Logout),
        ]

__all__ = ['URLS']
