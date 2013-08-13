from tornado.web import HTTPError
from mongoengine import ValidationError
from requires.base import BaseHandler, authenticated
from datamodels.user import User, Session, SessionManager

class UserHandler(BaseHandler):

    SUPPORTED_METHODS = ('GET','PUT','POST','DELETE')
    REQUIRED_FIELDS = {
        'PUT': ('username','password','email')
        }
    
    def put(self, *args, **kwargs):
        """
        Register a new user
        """
        data = self.data
        user = User(**data)
        # Password has to be hashed
        user.password = SessionManager.encryptPassword(user.password)
        
        try:
            user.save(validate=True, clean=True)
        except ValidationError, error:
            error_data = {
                'reason': error.to_dict()['__all__']
            }
            raise HTTPError(403, **error_data)
        
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
            user = User.objects.get(username=username)
            self.write(user.to_json())
        except User.DoesNotExist:
            self.send_error(404)

    def post(self, *args, **kwargs):
        pass

    def delete(self, *args, **kwargs):
        pass