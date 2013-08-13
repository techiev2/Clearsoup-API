import sys
sys.dont_write_bytecode = True

from requires.base import BaseHandler


class Main(BaseHandler):
    """
    Main request handler for core app.
    """

    def __init__(self, *args, **kwargs):
        """
        Main request handler init.
        """
        super(Main, self).__init__(*args, **kwargs)

    def get(self, *args, **kwargs):
        """
        HTTP GET Request handler method for Main handler.
        """
        # super(Main, self).get(*args, **kwargs)
        # self.write({
        #     'status': 'success',
        #     'endPoint': '/',
        #     'authorizationRequired': True,
        #     'message': 'Authorization required to access this endpoint'
        # })

    def post(self, *args, **kwargs):
        """
        HTTP POST Request handler method for Main handler.
        """
        super(Main, self).post(*args, **kwargs)
        self.write(self.data)


__all__ = ['Main']


if __name__ == '__main__':
    pass
