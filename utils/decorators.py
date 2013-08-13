"""
Utils.
"""

import sys
sys.dont_write_bytecode = True

from functools import wraps
import re
from hashlib import md5
try:
    import json
except ImportError:
    import simplejson as json

from datamodels.user import Session, User

FIRST_CAP_RE = re.compile('(.)([A-Z][a-z]+)')
ALL_CAP_RE = re.compile('([a-z0-9])([A-Z])')


def convert(name):
    """
    Convert camelcased strings to methodic strings.
    """
    str_1 = FIRST_CAP_RE.sub(r'\1_\2', name)
    return ALL_CAP_RE.sub(r'\1_\2', str_1).lower()


def get_user_session(cookie):
    try:
        session = Session.objects.get(state=cookie)
    except Session.DoesNotExist:
        session = None
    return session
        


def is_authenticated(method):
    """
    Basic authenticated check decorator.
    """
    
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper method for is_authenticated decorator.
        """
        cookie = self.get_cookie(self.settings['cookie'])
        if cookie:
            self.cookie = cookie
            self.session = get_user_session(self.cookie)
            if self.session:
                if not self.session.is_valid():
                    self.response = self.response_reauth
                else:
                    try:
                        self.user = User.objects.get(pk=cookie)
                    except User.DoesNotExist:
                        self.user = None
                        self.session = None
                        self.response = self.response = self.response_auth
            else:
                self.session = None
                self.user = None
                self.response = self.response_auth
        return method(self, *args, **kwargs)
    return wrapper


def serialize(method):
    """
    Serialize the incoming request and set class data member.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper for serialize decorator.
        """
        data = {}
        allowed = ['PUT', 'POST', "DELETE"]
        if self.request.method in allowed:
            try:
                data = json.loads(self.request.body)
                buff_data = {}
                for (key, value) in data.iteritems():
                    buff_data.update({
                        convert(key): value
                    })
                    self.data = buff_data
            except Exception, e:
                if self.request.body:
                    body = self.request.body.split('&')
                    for data_field in body:
                        key = data_field.split('=')[0]
                        val = data_field.split('=')[1]
                        if key == 'password':
                            val = md5(val).hexdigest()
                        data.update({
                            convert(key): val
                        })
                    self.data = data
        elif self.request.method == 'GET':
            process_data = self.request.uri.split('?')
            data = {}
            if len(process_data) == 2:
                process_data = process_data[1]
                body = process_data.split('&')
                for data_field in body:
                    key = data_field.split('=')[0]
                    val = data_field.split('=')[1]
                    if key == 'password':
                        val = md5(val).hexdigest()
                    data.update({
                        convert(key): val
                    })
            if self.data and isinstance(self.data, dict):
                self.data.update(data)
            else:
                self.data = data
        return method(self, *args, **kwargs)
    return wrapper


__all__ = ['is_authenticated', 'serialize']
