'''
Created on 12-Aug-2013

@author: someshs
'''

import sys
sys.dont_write_bytecode = True

import mongoengine as me
from datetime import datetime


class BaseModel(me.Document):
    meta = {
        'allow_inheritance': True
    }
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=False)
    updated_by = me.ReferenceField('User', required=False)
    is_active = me.BooleanField(default=True)

