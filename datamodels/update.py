import sys
from bson.json_util import default
sys.dont_write_bytecode = True

import mongoengine as me
import re

from mongoengine.base import ValidationError
from mongoengine import signals
from datetime import datetime
#from utils.dumpers import json_dumper

MENTION_REGEX = r'@[A-Za-z0-9_.-]+'
HASHTAG_REGEX = r'#[A-Za-z0-9_.-]+'
UPDATE_REGEX = '^[a-zA-Z0-9-_,;.\?\/\s]*$'

class Update(me.Document):
    # Meta
    created_by = me.ReferenceField('User', required=True, dbref=True)
    created_at = me.DateTimeField(default=datetime.utcnow())

    # Fields
    project = me.ReferenceField('Project', required=True, dbref=True)
    text = me.StringField(max_length=140, required=True)
    mentions = me.ListField(required=False)
    hashtags = me.ListField(required=False)

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        '''
            validating max length and mentioned user
        '''
        mentions = re.findall(MENTION_REGEX, document.text)
        if len(mentions) > 0:
            document.mentions = [mention[1:] for mention in mentions]
        if document.created_by not in document.project.members:
            raise ValidationError('You are not a member of this project')
        if len(document.text) > 140:
            raise ValidationError('Update exceeds 140 characters')


    def save(self, *args, **kwargs):
        # Explicitly set the date as mongo(engine|db) seems to
        # cache the date
        self.created_at = datetime.utcnow()
        # Extract list of mentions and hashtags
        # and save it
        mentions = re.findall(MENTION_REGEX, self.text)
        if len(mentions) > 0:
            self.mentions = [mention[1:] for mention in mentions]
        hashtags = re.findall(HASHTAG_REGEX, self.text)
        if len(hashtags) > 0:
            self.hashtags = [hashtag[1:] for hashtag in hashtags]
            self.project.hashtags.extend(self.hashtags)
            self.project.update(set__hashtags=set(self.project.hashtags))
        super(Update, self).save(*args, **kwargs)


class TaskUpdate(me.Document):
    # Meta
    created_by = me.ReferenceField('User', required=True, dbref=True)
    created_at = me.DateTimeField(default=datetime.utcnow())
    updated_by = me.ReferenceField('User', required=True, dbref=True)
    # Fields
    project = me.ReferenceField('Project', required=True)
    task = me.ReferenceField('Task', required=True)
    text = me.StringField(max_length=140, required=True)
    is_active = me.BooleanField(default=True)
    mentions = me.ListField(required=False)
    hashtags = me.ListField(required=False)


    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        '''
            validating max length and mentioned user
        '''
        mentions = re.findall(MENTION_REGEX, document.text)
        if len(mentions) > 0:
            document.mentions = [mention[1:] for mention in mentions]
        if document.created_by not in document.project.members:
            raise ValidationError('You are not a member of this project')
        if len(document.text) > 140:
            raise ValidationError('Update exceeds 140 characters')

    def save(self, *args, **kwargs):
        # Extract list of mentions and hashtags
        # and save it
        mentions = re.findall(MENTION_REGEX, self.text)
        if len(mentions) > 0:
            self.mentions = [mention[1:] for mention in mentions]
        hashtags = re.findall(HASHTAG_REGEX, self.text)
        if len(hashtags) > 0:
            self.hashtags = [hashtag[1:] for hashtag in hashtags]
            self.project.hashtags.extend(self.hashtags)
            self.project.update(set__hashtags=set(self.project.hashtags))
        super(TaskUpdate, self).save(*args, **kwargs)


signals.pre_save.connect(Update.pre_save, sender=Update)
signals.pre_save.connect(TaskUpdate.pre_save, sender=Update)
