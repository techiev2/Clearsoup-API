
import sys
sys.dont_write_bytecode = True

import ast
from datetime import datetime
import urllib

from requires.base import BaseHandler
from datamodels.session import Session, SessionManager


class Authenticate(BaseHandler):
    """
    Authenticates the username/password and generates
    a session token which is used for all other calls
    """

    SUPPORTED_METHODS = ('POST')
    
    REQUIRED_FIELDS   = {
        'POST': ('email','password')
        }

    def clean_oauth_data(self, oauth_data):
        return ast.literal_eval(urllib.unquote(oauth_data))

    def post(self, *args, **kwargs):
        """
        HTTP POST Request handler method.
        Authenticates the user, generates session token and sends
        it to the client
        """
        
        _oauth = None
        if self.get_argument('google_oauth', None):
            _oauth, _provider = self.get_argument('google_oauth', None), 'google'
        if self.get_argument('github_oauth', None):
            _oauth, _provider = self.get_argument('github_oauth', None), 'github'
        
        if _oauth:
            _oauth_data = self.clean_oauth_data(_oauth)
            email = _oauth_data['email']
            user = SessionManager.validateOauthLogin(email=email,
                                                     provider=_provider)
        else:
            user = SessionManager.validateLogin(email=self.get_argument('email'),
                                            username=self.get_argument('email'),
                                            password=self.get_argument('password'))
        if user:
            self.current_user = user
            # Create a new session by passing the handler to SessionManager
            # This is because we will be signing the token with RequestHandler.create_signed_value
            # to prevent tampering
            session = SessionManager.createSession(self)
            if session:
                self.write({
                    'status': 200,
                    'message': 'Authentication successful',
                    'token': session.signed_token,
                    'username': user.username
                    })
            else:
                self.send_error(500, 'Could not create a new session')
        else:
            self.write({
                'status': 403,
                'message': 'Incorrect username or password'
                })

class Logout(BaseHandler):
    """
    Session logout handler.
    """

    def __init__(self, *args, **kwargs):
        """
        Logout handler init.
        """
        super(Logout, self).__init__(*args, **kwargs)

    def get_session(self):
        """
        Get session data from cookies.
        """
        self.session = None
        self.cookie = self.get_cookie('state')
        if self.cookie:
            try:
                self.session = Session.objects.get(state=self.cookie)
            except Session.DoesNotExist:
                self.response = {
                    'status': 400,
                    'message': 'Invalid session.'
                }
            if len(self.session) == 1:
                self.session = self.session[0]

    def post(self, *args, **kwargs):
        """
        HTTP POST request handler method for Clearsoup api
        logout end point.
        """
        super(Logout, self).post(*args, **kwargs)
        if not self.data:
            self.response = self.response_400
        else:
            self.get_session()
            if self.session:
                self.session.update(set__ended=datetime.utcnow(),
                                    set__active=False)
                self.response = {
                    'status': 200,
                    'message': 'Logout operation successful'
                }
            else:
                self.response = {
                    'status': 302,
                    'message': 'No valid session found.'
                }

        if self.response:
            self.finish(self.response)

    def get(self, *args, **kwargs):
        """
        HTTP GET Request handler method for logout end point.
        """
        super(Logout, self).get(*args, **kwargs)
        self.write(self.response_405)


__all__ = ['Authenticate', 'Register', 'Logout']
