'''
Created on 24-Oct-2013

@author: someshs
'''
import json
from tornado.web import HTTPError

from requires.base import BaseHandler, authenticated
from datamodels.user import User
from datamodels.userprofile import UserProfile


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
            print self.data
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
            response['user'] = self.current_user.to_json()
            response['profile'] = self.current_user.profile.to_json(exclude='password')
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
        print response
        self.write(json.dumps(response))
