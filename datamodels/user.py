import sys
sys.dont_write_bytecode = True

import os
import pymongo
import mongoengine as me

from mongoengine.base import ValidationError


from organization import Organization
from userprofile import UserProfile
from utils.dumpers import  json_dumper

sys.dont_write_bytecode = True


class User(me.Document):
    username = me.StringField(max_length=32,
                              unique=True, required=True)
    password = me.StringField(required=True)
    email = me.EmailField(required=True, unique=True)
    # Profile
    profile = me.ReferenceField(UserProfile)
    # Org
    belongs_to = me.ListField(me.ReferenceField('Organization'))


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
        elif len(User.objects.filter(email=self.email)) > 0:
            raise ValidationError('Email already exists')

    def update_profile(self, google_oauth):
        if google_oauth and isinstance(google_oauth, dict):
            user_profile = UserProfile(google=google_oauth)
            user_profile.save()
            self.update(set__profile=user_profile)

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(User, self).update(*args, **kwargs)
        self.reload()


if __name__ == '__main__':
    pass
