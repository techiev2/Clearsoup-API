import sys
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
    project = me.ReferenceField('Project', required=True)
    text = me.StringField(max_length=140, required=True)
    mentions = me.ListField(required=False)
    hashtags = me.ListField(required=False)

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
            self.project.hashtags.append(self.hashtags)
            self.project.update(set__hashtags=set(self.project.hash_tag))
        super(Update, self).save(*args, **kwargs)


class TaskUpdate(me.Document):
    # Meta
    created_by = me.ReferenceField('User', required=True, dbref=True)
    created_at = me.DateTimeField(default=datetime.utcnow())
    updated_by = me.ReferenceField('User', required=True, dbref=True)
    # Fields
    project = me.ReferenceField('Project', required=True)
    task = me.ReferenceField('Task', required=True)
    text = me.StringField(max_length=140, required=True, regex=UPDATE_REGEX)
    mentions = me.ListField(required=False)
    hashtags = me.ListField(required=False)

    def save(self, *args, **kwargs):
        # Extract list of mentions and hashtags
        # and save it
        mentions = re.findall(MENTION_REGEX, self.text)
        if len(mentions) > 0:
            self.mentions = [mention[1:] for mention in mentions]
        hashtags = re.findall(HASHTAG_REGEX, self.text)
        if len(hashtags) > 0:
            self.hashtags = [hashtag[1:] for hashtag in hashtags]
            self.project.hashtags.append(self.hashtags)
            self.project.update(set__hashtags=set(self.project.hash_tag))
        super(TaskUpdate, self).save(*args, **kwargs)

