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

    first_name = me.StringField(max_length=30)
    last_name = me.StringField(max_length=30)
    google = me.DictField()
    github = me.DictField()
    avatar = me.URLField()
    facebook_handle = me.StringField(max_length=100)
    twitter_handle = me.StringField(max_length=100)
    linkedin_handle = me.StringField(max_length=100)
    description = me.StringField(max_length=500)
    company = me.StringField(max_length=100)
    designation = me.StringField(max_length=100)
    mobile = me.IntField()

    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=False)
    updated_by = me.ReferenceField('User', required=False)
    is_active = me.BooleanField(default=True)

    def __str__(self):
        return ' '.join([self.first_name, self.last_name])

    def __init__(self, *args, **kwargs):
        super(UserProfile, self).__init__(*args, **kwargs)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        if document.google:
            if UserProfile.objects.filter(
                          google__email=document.google['email']).count() > 0:
                raise ValidationError('This account is already registered.')
        if document.github:
            if UserProfile.objects.filter(
                          github__email=document.github['email']).count() > 0:
                raise ValidationError('This account is already registered.')
        if document.description and len(document.description) > 500:
            raise ValidationError('Description exceeds 500 characters')
        if document.facebook_handle and len(document.facebook_handle) > 100:
            raise ValidationError('Facebook id exceeds 100 characters')
        if document.twitter_handle and len(document.twitter_handle) > 100:
            raise ValidationError('Twitter id exceeds 100 characters')
        if document.linkedin_handle and len(document.linkedin_handle) > 100:
            raise ValidationError('Linked-in id exceeds 100 characters')
        if document.company and len(document.company) > 100:
            raise ValidationError('Company exceeds 100 characters')
        if document.desingation and len(document.desingation) > 100:
            raise ValidationError('Designation exceeds 100 characters')
        if document.first_name and len(document.first_name) > 30:
            raise ValidationError('First name exceeds 30 characters')
        if document.last_name and len(document.last_name) > 30:
            raise ValidationError('Last name exceeds 30 characters')
        if document.mobile and len(str(document.mobile)) > 13:
            raise ValidationError('Mobile number exceeds 13 characters')

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        if not document.first_name and not document.last_name:
            first_name = last_name = ''
            if document.google:
                if 'first_name' in document.google.keys(): 
                    first_name = document.google['first_name']
                if 'last_name' in document.google.keys():
                    last_name = document.google['last_name']
            if document.github:
                try:
                    first_name, last_name = document.github['name'].split(' ')
                except ValueError:
                    first_name, last_name = document.github['name'], ''
                except KeyError:
                    pass
            document.update(set__first_name=first_name,
                            set__last_name=last_name)

    def save(self, *args, **kwargs):
        super(UserProfile, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(UserProfile, self).update(*args, **kwargs)
        self.reload()

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)


signals.pre_save.connect(UserProfile.pre_save, sender=UserProfile)
signals.post_save.connect(UserProfile.post_save, sender=UserProfile)
