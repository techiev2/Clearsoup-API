'''
Created on 12-Aug-2013

@author: someshs
'''
import sys
sys.dont_write_bytecode = True
from datetime import datetime

import mongoengine as me
from utils.dumpers import json_dumper


class Organization(me.Document):
    name = me.StringField(required=True, max_length=64)
    admin = me.ListField(me.ReferenceField('User'))
    url = me.URLField(required=False, unique=True)
    
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=False)
    updated_by = me.ReferenceField('User', required=False)
    is_active = me.BooleanField(default=True)

    meta = {
        'indexes': ['name']
        }

    
    def __str__(self):
        return self.name
    
    def to_json(self, fields, exclude):
        return json_dumper(self, fields, exclude)