'''
Created on 24-Oct-2013

@author: someshs
'''
import json
from tornado.web import HTTPError

from requires.base import BaseHandler, authenticated
from datamodels.user import User, PasswordResetToken
from datamodels.userprofile import UserProfile
from datamodels.session import SessionManager
from mongoengine.errors import NotUniqueError


class ProfileHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST',)
    REQUIRED_FIELDS   = {
        'POST': ('username', ),
        'GET': ('username', )
        }
    data = {}
    
    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        session_user = None
        try:
            session_user = User.objects.get(username=self.data['username'])
            if session_user != self.current_user:
                raise HTTPError(403, **{'reason': "Not authorized to edit profile."})
        except User.DoesNotExist:
            raise HTTPError(404, **{'reason': "User not found"})
        self.data['updated_by'] = self.current_user

    @authenticated
    def get(self, *args, **kwargs):
        username = self.get_argument('username')
        response = {}
        try:
            user = User.objects.get(username=username)
            response['is_edit'] = False
            if user == self.current_user:
                response['is_edit'] = True
            response['user'] = user.to_json()
            response['profile'] = user.profile.to_json(exclude='password')
            self.finish(response)
        except User.DoesNotExist:
            raise HTTPError(404, **{'reason': "User not found"})
        


    @authenticated
    def post(self, *args, **kwargs):
        self.clean_request()
        profile = self.current_user.profile
        response = {}
        temp_data = {'set__'+field: self.data[field] for field
                         in UserProfile._fields.keys()
                         if field in self.data.keys()}
        profile.update(**temp_data)
        response['profile'] = profile.to_json()

        response['user'] = self.current_user.to_json()
        self.write(json.dumps(response))


class ResetPasswordHandler(BaseHandler, object):

    REQUIRED_FIELDS = {
        'POST': ('password', 'token',)
    }

    """Reset password handler"""
    def __init__(self, *args, **kwargs):
        """Reset password handler class init"""
        super(ResetPasswordHandler, self).__init__(*args, **kwargs)

    def post(self, *args, **kwargs):
        response = {}
        if 'password' in self.data.iterkeys() \
                and 'token' in self.data.iterkeys():
            token = PasswordResetToken.objects.filter(
                token=self.data.get('token'))
            if token.count() == 1:
                self.current_user = token[0].user
                temp_data = {'set__password': SessionManager.encryptPassword(
                    self.data.get('password'))}
                self.current_user.update(**temp_data)
                token.delete()
            elif token.count() == 0:
                self.send_error(404)
                return
            else:
                self.send_error(403)
                return
        else:
            self.send_error(400)
            return

        response['user'] = self.current_user.to_json()
        self.write(json.dumps(response))

    def put(self, *args, **kwargs):
        """HTTP PUT request handler method for ResetPasswordHandler"""
        if not (len(self.data.keys()) == 1 and self.data.get(
                'email')):
            self.send_error(400)
        user = User.objects.filter(email=self.data.get('email'))
        user = user[0] if user.count() == 1 else None
        if user:
            try:
                token = PasswordResetToken(user=user)
                token.save()
                self.write(token.to_json())
            except NotUniqueError:
                token = PasswordResetToken.objects.filter(user=user)
                if token.count() == 1:
                    token[0].reset_token()
                    self.write(token[0].to_json())
                else:
                    self.send_error(400)
                    return
        else:
            self.write({})
