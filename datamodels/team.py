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
from datamodels.permission import Role
from utils.dumpers import json_dumper
from requires.settings import ADMIN_ROLES, TEAM_ROLES


class Team(me.Document):
    '''
    '''
    project = me.ReferenceField('Project', required=True,
                                reverse_delete_rule=me.CASCADE,
                                dbref=True)
    role = me.ReferenceField('Role', dbref=True,
                             reverse_delete_rule=me.CASCADE,)
    user = me.ReferenceField('User', required=True, dbref=True,
                             reverse_delete_rule=me.CASCADE,)
    
    created_by = me.ReferenceField('User', required=True,
                                   reverse_delete_rule=me.CASCADE,)
    updated_by = me.ReferenceField('User', required=True,
                                   reverse_delete_rule=me.CASCADE,)
    created_at = me.DateTimeField(default=datetime.utcnow())
    updated_at = me.DateTimeField(default=datetime.utcnow())

    def __init__(self, *args, **values):
        super(Team, self).__init__( *args, **values)

    def __str__(self):
        return self.project.title

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)

    @classmethod
    def create_team(cls , project=None, user=None):
        role = Role.objects.get(role='Administrator', project=project)
        t = Team(project=project,
                 role=role,
                 user=user,
                 created_by=user,
                 updated_by=user)
        t.save()

    def save(self, *args, **kwargs):
        super(Team, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(Team, self).update(*args, **kwargs)
        self.reload()


