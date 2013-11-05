import sys
sys.dont_write_bytecode = True
import re
import mongoengine as me
from mongoengine.base import ValidationError

from organization import Organization
from userprofile import UserProfile
from utils.dumpers import  json_dumper
from requires.settings import SETTINGS

sys.dont_write_bytecode = True

USERNAME_REGX = re.compile('[a-zA-Z0-9-_\.]*$')
EMAIL_REGX = re.compile('[a-zA-Z0-9_.-@]*$')

class User(me.Document):
    username = me.StringField(max_length=32,
                              unique=True, required=True)
    password = me.StringField(required=True)
    email = me.EmailField(required=True, unique=True)
    # Profile
    profile = me.ReferenceField('UserProfile', dbref=True)
    # Org
    belongs_to = me.ListField(me.ReferenceField('Organization'))
    roles = me.DictField(default={})

    meta = {
        "indexes": ["username", "email"]
    }

    def __str__(self):
        return unicode(self.username)

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)
    
    def clean(self):
        if len(User.objects.filter(username=self.username)) > 0:
            raise ValidationError('Username already exists')
        if len(User.objects.filter(email=self.email)) > 0:
            raise ValidationError('Email already exists')
        if USERNAME_REGX is not None and USERNAME_REGX.match(
                 self.username) is None:
            raise ValidationError('Special characters not allowed in username.')

    def update_profile(self, _oauth=None, _provider=None):
        data_dict = {}
        if _oauth and isinstance(_oauth, dict):
            _oauth_dict = {}
            _oauth_dict = {_provider: _oauth}
            data_dict.update({_provider: _oauth})
        data_dict['created_by'] = self
        data_dict['updated_by'] = self
        data_dict['avatar'] = SETTINGS['default_avatar']
        user_profile = UserProfile(**data_dict)
        user_profile.save()
        self.update(set__profile=user_profile)

    def update_organization_list(self, organization=None):
        if not self.belongs_to:
            self.update(set__belongs_to=[organization])
        else:
            self.belongs_to.append(organization)
            self.update(set__belongs_to=self.belongs_to)

    def get_user_profile(self):
        return UserProfile.objects.filter(user=self)

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(User, self).update(*args, **kwargs)
        self.reload()


if __name__ == '__main__':
    pass

