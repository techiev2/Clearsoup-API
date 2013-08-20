'''
Created on 16-Aug-2013

@author: someshs
'''

from datetime import datetime, timedelta
import sys
sys.dont_write_bytecode = True

import mongoengine as me
from mongoengine.base import ValidationError
from mongoengine import signals
from datamodels.user import User
from datamodels.project import Project
from utils.dumpers import json_dumper


class ProjectPermission(me.Document):
    
    '''
    map for the project owner will be 2047 and for person added to project 
    will be 0.
    2047 as there are 11 different privilege.
    '''
    # edit fields will include deletion of the entity
    user = me.ReferenceField('User', required=True)
    project = me.ReferenceField('Project', required=True)
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

    def save(self, *args, **kwargs):
        super(ProjectPermission, self).save(*args, **kwargs)
        self.reload()
    
    def update(self, *args, **kwargs):
        super(ProjectPermission, self).update(*args, **kwargs)
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


