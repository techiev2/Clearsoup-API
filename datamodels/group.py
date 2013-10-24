'''
Created on 22-Aug-2013

@author: someshs
'''

from datetime import datetime
import sys
sys.dont_write_bytecode = True

import mongoengine as me
from mongoengine.base import ValidationError
from mongoengine import signals
from datamodels.project import Project
from datamodels.user import User
from utils.dumpers import json_dumper
from requires.settings import ADMIN_ROLES, TEAM_ROLES


class Group(me.Document):
    '''
        One role can't be in more than one group.

        map for the project owner will be 2047 and for person added to project 
        will be 0.
        2047 as there are 11 different privilege.
        
        Default groups as 'administrator and team member will be created
        when a project is created.'
    '''
    
    name = me.StringField(max_length=250)
    project = me.ReferenceField('Project', required=True,
                                reverse_delete_rule=me.CASCADE)
    roles = me.ListField()
    map = me.IntField(default=0)
    created_by = me.ReferenceField('User', required=True)
    updated_by = me.ReferenceField('User', required=True)
    created_at = me.DateTimeField(default=datetime.utcnow())
    updated_at = me.DateTimeField(default=datetime.utcnow())
    
    meta = {
        'indexes': ['name']
        }

    def __init__(self, *args, **values):
        super(Group, self).__init__( *args, **values)

    def __str__(self):
        return self.name

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

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)

    def clean(self):
        if Group.objects.filter(name=self.name,
                                project=self.project).count() > 0:
            raise ValidationError('Duplicate group')

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        '''
        1. check if group already exists,
        2. create default data for groups
        '''
        if len(document.name) > 250:
            raise ValidationError('Group exceeds 250 characters')

    @classmethod
    def create_initial_project_group(cls, project=None, user=None):
        Group.objects.create(name='Administrator', project=project,
                             created_by=user, updated_by=user,
                             roles=ADMIN_ROLES,
                             map=2047)
        Group.objects.create(name='Team Members', project=project,
                             created_by=user, updated_by=user, 
                             roles=TEAM_ROLES,
                             map=283)

    def save(self, *args, **kwargs):
        '''
            call save only in case of project PUT.
        '''
        super(Group, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(Group, self).update(*args, **kwargs)
        self.reload()

signals.pre_save.connect(Group.pre_save, sender=Group)

