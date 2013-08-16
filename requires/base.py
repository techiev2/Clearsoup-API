"""
Base Handlers
This overrides tornado.web.RequestHandler to add custom
validation and utilities to our Handlers
"""
import sys
sys.dont_write_bytecode = True

import base64
import tornado.escape
from tornado.web import HTTPError, MissingArgumentError
from functools import wraps

from datamodels.session import SessionManager 


CONTENT_TYPES = {
    'json': 'application/json'
}

class BaseHandler(tornado.web.RequestHandler):

    def initialize(self):
        self.data = {}

    def prepare(self):
        """
        Unforunately, if the request body is json, tornado doesn't
        handle it. We need to decode the body, and serialize it and
        store it as self.data for passing directly to models if required
        """
        method = self.request.method
        if ((method == 'PUT' or method == 'POST') and
                self.request.headers.get("Content-Type") == "application/json" and
                self.request.body is not None and
                self.request.body.strip()):
            try:
                args = tornado.escape.json_decode(self.request.body)
                # RequestHandler.request.arguments is a dict where every value
                # is a list. This is handled internally when using
                # RequestHandler.get_argument. We need to make sure that our
                # json arguments are also available as a list, else tornado
                # will truncate the arguments
                for k in args.keys():
                    args[k] = [args[k]]
                self.request.arguments.update(args)
            except ValueError:
                pass
        # self.data is populated with all arguments sent in a request:
        # query params and request body
        self.data = self.request.arguments.copy()
        for k in self.data.keys():
            if isinstance(self.data[k], list) and len(self.data[k]) == 1:
                self.data[k] = self.data[k][0]

        # If the handler has a set of required fields, validate that
        if (hasattr(self, 'REQUIRED_FIELDS') and
                method in self.REQUIRED_FIELDS):
            self.validate_required_fields(self.REQUIRED_FIELDS[method])


    def validate_required_fields(self, required_fields):
        fields = self.request.arguments
        if len(fields) == 0 or not all(field in fields for field in required_fields):
            kwargs = {
                'reason': 'Required parameters missing'
                }
            raise tornado.web.HTTPError(403, **kwargs)

    def error_message(self, error):
        '''
        Return a readable error message.
        '''       
        if hasattr(error, 'to_dict'):
            if error.to_dict().values():
                message = error.to_dict().values()[0]
            else:
                message = error.message
        else:
            message = error.message
        return str(message)

    def write_error(self, status_code, **kwargs):
        """
        Override the base write_error method to output
        all the errors in JSON. The appropriate status code is also set
        in the response along with the error message
        """
        message = self._reason
        # Check if error info is available
        if 'exc_info' in kwargs:
            stack = kwargs['exc_info']
            if stack and 'reason' in stack[1]:
                message = stack[1].reason

        self.set_header("Content-Type", "application/json")
        self.set_status(status_code)
        self.finish({
            "status": status_code,
            "message": message
            })


    def get_current_user(self):
        """ 
        Load the user from the session token
        Used by tornado.web.authenticated decorator
        """
        signed_token = self.get_argument('token', None)
        # If not, try the cookie
        signed_token = signed_token or self.get_cookie('token', None)
        # If we have a token
        if signed_token:
            # Decode the token
            token = self.get_secure_cookie('token', signed_token)
            if token:
                # Verify if the session exists and is valid
                session = SessionManager.loadSession(token)
                if session:
                    return session.user
            return None
        # Try basic auth
        else:
            return self.basic_auth()

    def basic_auth(self):
        auth_header = self.request.headers.get("Authorization", None)
        if auth_header is not None and auth_header.startswith('Basic'):
            try:
                auth_decoded = base64.decodestring(auth_header[6:])
                username, password = auth_decoded.split(':', 2)
                # Validate and return user
                return SessionManager.validateLogin(username=username, 
                                                    password=password)
            except Exception:
                return None
        return None


def authenticated(method):
    """
    Modified version of tornado.web.authenticated to prevent
    redirection as this is used in the API
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if not self.current_user:
            raise HTTPError(403, 'Invalid session token')
        return method(self, *args, **kwargs)
    return wrapper
