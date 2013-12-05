from admin.handlers import AdminHandler

URLS = [('/api/_su_/?$', AdminHandler)
        ]

__all__ = ['URLS']
