'''
Created on 16-Aug-2013

@author: someshs
'''

import sys
sys.dont_write_bytecode = True
from datetime import datetime
import mongoengine as me
from datamodels.user import User
from datamodels.project import Project
from utils.dumpers import json_dumper


class Role(me.Document):
    '''
        
    '''
    project = me.ReferenceField('Project', required=True, dbref=True,
                                reverse_delete_rule=me.CASCADE,)
    role = me.StringField()
    map = me.IntField(default=0)
    created_by = me.ReferenceField('User', required=True, dbref=True,
                                   reverse_delete_rule=me.CASCADE,)
    updated_by = me.ReferenceField('User', required=True, dbref=True,
                                   reverse_delete_rule=me.CASCADE,)
    created_on = me.DateTimeField(default=datetime.utcnow())
    updated_on = me.DateTimeField(default=datetime.utcnow())
    
    def __str__(self):
        return self.role

    # testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
    @classmethod
    def testBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type & mask)

    # setBit() returns an integer with the bit at 'offset' set to 1.
    @classmethod
    def setBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type | mask)

    # clearBit() returns an integer with the bit at 'offset' cleared.
    @classmethod
    def clearBit(cls, int_type, offset):
        mask = ~(1 << offset)
        return(int_type & mask)

    # toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.
    @classmethod
    def toggleBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type ^ mask)
    
    @classmethod
    def create_role_map(cls, new_roles, project, user, map):
        for role in new_roles:
            Role.objects.create(project=project,
                                role=role,
                                created_by=user,
                                updated_by=user,
                                map=map)

    def save(self, *args, **kwargs):
        super(Role, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(Role, self).update(*args, **kwargs)
        self.reload()

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)


class OrganizationPermission(me.Document):
    user = me.ReferenceField('User', required=True)
    organization = me.ReferenceField('Organization', required=True)
    map = me.IntField(default=0)

    # testBit() returns a nonzero result, 2**offset, if the bit at 'offset' is one.
    @classmethod
    def testBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type & mask)
    
    # setBit() returns an integer with the bit at 'offset' set to 1.
    @classmethod
    def setBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type | mask)
    
    # clearBit() returns an integer with the bit at 'offset' cleared.
    @classmethod
    def clearBit(cls, int_type, offset):
        mask = ~(1 << offset)
        return(int_type & mask)
    
    # toggleBit() returns an integer with the bit at 'offset' inverted, 0 -> 1 and 1 -> 0.
    @classmethod
    def toggleBit(cls, int_type, offset):
        mask = 1 << offset
        return(int_type ^ mask)


