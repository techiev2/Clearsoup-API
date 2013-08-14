'''
Created on 12-Aug-2013

@author: someshs
'''

import sys
from datetime import datetime
from fysom import Fysom

import mongoengine as me

from utils.dumpers import json_dumper

sys.dont_write_bytecode = True


TASK_TYPES = ['Design', 'Development', 'Review', 'Testing', 'Documentation']

states = {
    'default': {
        'initial': 'New',
        'events': [
            { 'name': 'assign', 'src': 'New', 'dst': 'Pending' },
            { 'name': 'start', 'src': 'Pending', 'dst': 'InProgress' },
            { 'name': 'close', 'src': 'InProgress', 'dst': 'Closed' }
        ]
    },
    'review': {
        'initial': 'New',
        'events': [
            { 'name': 'assign', 'src': 'New', 'dst': 'Pending' },
            { 'name': 'start', 'src': 'Pending', 'dst': 'InProgress' },
            { 'name': 'submitForReview', 'src': 'InProgress', 'dst': 'ForReview', 'action': {'method': 'create', 'entity': 'Task', 'args':{'type': 'Review'} } },
            { 'name': 'reviewPass', 'src': 'ForReview', 'dst': 'Reviewed' },
            { 'name': 'reviewFail', 'src': 'ForReview', 'dst': 'ReviewFail' },
            { 'name': 'fix', 'src': 'ReviewFail', 'dst': 'Fixed' },
            { 'name': 'close', 'src': ['InProgress','Reviewed','Fixed'], 'dst': 'Closed' }
        ]
    }
}


class Task(me.Document):
    """
    Task model is also a finite state machine, which is used to 
    determine the state flow for a customizable workflow
    Since multiple inheritance in python is kind of a gray area, we
    are avoiding it and instead instantiating a state property which
    holds the state machine, its properties and methods
    """
    # def __init__(self, *args, **kwargs):
    #     self._state = Fysom(states['default'])

    task_type = me.StringField(choices=TASK_TYPES, required=True),
    seq_id = me.SequenceField(),
    title = me.StringField(max_length=128),
    description = me.StringField(),
    assigned_to = me.ReferenceField('User'), #Change to User
    estimated_completion = me.DateTimeField(required=False),
    actual_completion = me.DateTimeField(required=False)
    #current_action: basestring, #Change to TaskAction
    
    # Either parent task or child tasks
    #'parent_task': Task,
    #'child_tasks': [Task]
    
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=False)
    updated_by = me.ReferenceField('User', required=False)
    is_active = me.BooleanField(default=True)

    def validate(self, *args, **kwargs):
        # try:
        if hasattr(self, "_state_machine"):
            delattr(self, "_state_machine")
        super(Task, self).validate()
        # except Exception, e:
        #     if e.message.find("_dynamic_fields") != -1 or\
        #        e.message.find("_data") != -1:
        #         print '_dynamic_fields error passed'
        #     else:
        #         raise e

    @property
    def state_machine(self):
        if not hasattr(self, "_state_machine"):
            self._state_machine = Fysom(states['default'])
        return self._state_machine

    def onchangestate(self, e):
        print 'Changing task from ' + e.src + ' to ' + e.dst
        # Change current action to next action
        self.current_action += 1

    def next(self):
        getattr(self, self.actions[self.current_action])()

    def to_json(self, fields, exclude):
        return json_dumper(self, fields, exclude)


class EntityFactory:
    """
    Factory to create and return entities of specified type
    """

    ALLOWED_ENTITIES = ['Task','Story']

    @staticmethod
    def create(entity_type, **kwargs):
        # Get reference to the current module (basemodel)
        module = sys.modules[__name__]
        # If we are allowed to create the entity
        if entity_type in EntityFactory.ALLOWED_ENTITIES and hasattr(module, entity_type):
            try:
                # Try and create a new instance of the entity
                return getattr(module, entity_type)(**kwargs)
            except NameError:
                return None
        return None

    @staticmethod
    def get(entity_type, id):
        pass


class WorkflowDispatcher:
    """
    This class handles all the action attributes of a state transition
    It invokes the entitiy factory to get the required entity and then performs
    the required action on it
    """
    pass

