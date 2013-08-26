import ast
import urllib

from tornado.web import HTTPError
from mongoengine import ValidationError
from mongoengine.queryset import Q
from requires.base import BaseHandler, authenticated
from datamodels.session import SessionManager
from datamodels.user import User
from asyncmail import AsycnEmail
from datamodels.organization import Organization
from datamodels.project import Project
from utils.dumpers import json_dumper


class UserHandler(BaseHandler):

    SUPPORTED_METHODS = ('GET','PUT','POST','DELETE')
    REQUIRED_FIELDS = {
        'PUT': ('username','password','email')
        }
    
    def clean_oauth_data(self, oauth_data):
        return ast.literal_eval(urllib.unquote(oauth_data))

    def put(self, *args, **kwargs):
        print 27
        """
        Register a new user
        """
        data = self.data
        google_oauth = None
        if 'google_oauth' in data.keys():
            google_oauth = self.clean_oauth_data(data['google_oauth'])
            data.pop('google_oauth')
        
        user = User(**data)
        # Password has to be hashed
        user.password = SessionManager.encryptPassword(user.password)
        
        try:
            user.save(validate=True, clean=True)
            user.update_profile(google_oauth)
#            async_email = AsycnEmail(self.request)
#            async_email.generate_publish_content(user=user)
#            async_email.send_email(email=user.email)
        except ValidationError, error:
            raise HTTPError(403, **{'reason': self.error_message(error)})
        
        if user:
            self.finish({
                'status': 200,
                'message': 'User registered successfully'
            })

    @authenticated
    def get(self, username, *args, **kwargs):
        if not username:
            username = self.current_user.username
        try:
            response = {}
            user = User.objects.get(username=username)
            response['organization'] = [org.name for org in user.belongs_to]
            response['user'] = user.to_json()
            self.write(response)
        except User.DoesNotExist:
            self.send_error(404)

    def post(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass


