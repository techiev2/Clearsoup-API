from handlers import AppWebSocketHandler

URLS = [('/_socket', AppWebSocketHandler),
        ]

__all__ = ['URLS']

if __name__ == '__main__':
    pass
