'''
Created on 12-Aug-2013

@author: someshs
'''

import sys
from datetime import datetime

import mongoengine as me
from mongoengine import signals
from utils.dumpers import json_dumper
from mongoengine.errors import ValidationError

sys.dont_write_bytecode = True


class UserProfile(me.Document):
    """
    User profile model which has other social data and related
    user info
    """

    first_name = me.StringField()
    last_name = me.StringField()
    google = me.DictField()

    avatar = me.ImageField()

    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=False)
    updated_by = me.ReferenceField('User', required=False)
    is_active = me.BooleanField(default=True)

    def __str__(self):
        return ''.join([self.first_name, self.last_name])

    def __init__(self, *args, **kwargs):
        super(UserProfile, self).__init__(*args, **kwargs)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if UserProfile.objects.filter(
                      google__email=document.google['email']).count() > 0:
            raise ValidationError('This account is already registered.')
    
    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if not document.first_name and not document.last_name:
            document.update(set__first_name=document.google['first_name'],
                            set__last_name=document.google['last_name'])
    
    def save(self, *args, **kwargs):
        super(UserProfile, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(UserProfile, self).update(*args, **kwargs)
        self.reload()

    def to_json(self, fields, exclude):
        return json_dumper(self, fields, exclude)


signals.pre_save.connect(UserProfile.pre_save, sender=UserProfile)
signals.post_save.connect(UserProfile.post_save, sender=UserProfile)
