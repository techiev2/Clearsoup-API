'''
Created on 12-Aug-2013

@author: someshs
'''

import os
from datetime import datetime, timedelta
from passlib.hash import bcrypt
import pymongo

import mongoengine as me
from mongoengine.queryset import Q
from datamodels.user import User
from utils.dumpers import json_dumper

class Session(me.Document):
    """
    Everytime a user authenticates, a session is generated
    This contains a random alpha numeric session token that
    has to be passed for every request (either as a cookie or HTTP
    basic auth)
    """
    token = me.StringField(required=True)
    generated_at = me.DateTimeField(default=datetime.utcnow())
    user = me.ReferenceField('User')
    remote_ip = me.StringField()
    started = me.DateTimeField()
    expires = me.DateTimeField()
    ended = me.DateTimeField()
    is_active = me.BooleanField(default=True)

    def get_user(self, *args, **kwargs):
        """
        Get session user.
        """
        try:
            user = User.objects.get(pk=self.user)
        except User.DoesNotExist:
            user = None

        return user

    def is_valid(self, *args, **kwargs):
        """
        Return validity state of session.
        """
        diff = (self.expires - datetime.utcnow())
        return diff.days >= 0 and self.active

    def save(self, *args, **kwargs):
        '''
        Overridden save method to update reference to session User.
        '''
        try:
            now = datetime.utcnow()
            expires = now + timedelta(days=7)
            # user = User.objects.get(pk=uid)
            # self.user = user
            self.started = now
            self.expires = expires
            super(Session, self).save(*args, **kwargs)
            self.reload()
        except User.DoesNotExist:
            raise pymongo.errors.InvalidId

    def to_json(self, fields=None, exclude=None):
        """
        Return JSON interpretation of object instance.
        """
        return json_dumper(self, fields, exclude)


class SessionManager:
    """
    Session manager
    """

    @staticmethod
    def createSession(handler):
        session = Session()
        # Generate a signed token
        token = os.urandom(16).encode('hex')
        session.signed_token = handler.create_signed_value('token', token)
        session.token = token
        # Set the user
        session.user = handler.current_user
        try:
            session.save()
        except Exception, e:
            return None
        return session

    @classmethod
    def validateOauthLogin(cls, email=None, provider=None):
        if not email:
            return False
        # Check if user exists
        try:
            user = User.objects.get(email=email)
            if provider == 'google':
                if user and user.profile.google['email'] == email:
                    return user
            elif provider == 'github':
                if user and user.profile.github['email'] == email:
                    return user
            else:
                return False
        except User.DoesNotExist:
            return False

    @classmethod
    def validateLogin(cls, username=None, email=None, password=None):
        if password is None or (username is None and email is None):
            return False
        # Check if user exists
        try:
            user = User.objects.get(Q(email=email) | Q(username=username))
            if user and bcrypt.verify(password, user.password):
                return user
            else:
                return False
        except User.DoesNotExist:
            return False

    @staticmethod
    def loadSession(token):
        try:
            session = Session.objects.get(token=token)
        except Session.DoesNotExist:
            session = None
        return session

    @staticmethod
    def encryptPassword(password):
        return bcrypt.encrypt(password)

    @staticmethod
    def verifyPassword(password, hash):
        return bcrypt.verify(password, hash)
