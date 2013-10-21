'''
Created on 07-Aug-2013

@author: someshs
'''


import sys
sys.dont_write_bytecode = True
from datetime import datetime

import mongoengine as me
from mongoengine.base import ValidationError
from mongoengine import signals

from datamodels.project import Project, Sprint
from datamodels.analytics import ProjectMetadata
from utils.dumpers import json_dumper

TITLE_REGEX = '^[a-zA-Z0-9-_\.]*$'
DESCRIPTION_REGEX = '^[a-zA-Z0-9-_,;.\?\/\s]*$'
PRIORITIES = ["L", "M", "H", "X"]


class Story(me.Document):
    
    project = me.ReferenceField('Project',
                                reverse_delete_rule=me.CASCADE,
                                required=True,
                                dbref=True)
    sprint = me.ReferenceField(Sprint,
                               required=False,
                               reverse_delete_rule=me.CASCADE,
                               dbref=True)
    
    title = me.StringField(required=True,
                             max_length=128)
    priority = me.StringField(choices=PRIORITIES)
    description = me.StringField(max_length=500,
                                required=False)
    sequence = me.IntField(unique_with='project')
    status = me.StringField()

    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)
    created_by = me.ReferenceField('User', required=True, dbref=True)
    updated_by = me.ReferenceField('User', required=True, dbref=True)
    is_active = me.BooleanField(default=True)

    meta = {
        'indexes': ['title', 'project', 'sequence']
    }

    def __str__(self):
        return str(self.title)

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)

    def clean(self):
        if Story.objects.filter(title=self.title,
                                project=self.project,
                                is_active=True).count() > 0:
            raise ValidationError('Duplicate Story')

    @classmethod
    def last_story_id(cls, project):
        sequence = None
        stories = Story.objects.filter(project=project).order_by('sequence')
        if stories:
            sequence = list(stories)[-1].sequence
        return sequence

    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        '''
        1. check if Story already exists,
        2. create id for Story
        '''
        last_sequence = cls.last_story_id(document.project)
        if last_sequence:
            document.sequence = last_sequence + 1
        else:
            document.sequence = 1
        if document.created_by not in document.project.admin:
            raise ValidationError('You are not admin of this project')
        if len(document.title) > 128:
            raise ValidationError('Story exceeds 128 characters')
        if document.description and len(document.description) > 500:
            raise ValidationError('Story description exceeds 500 characters')

    @classmethod
    def post_save(cls, sender, document, **kwargs):
        '''
            1. update sequence value
        '''
        if document.sequence:
            document.update(set__sequence=document.sequence)

    def save(self, *args, **kwargs):
        '''
            call save only in case of Story PUT.
            for any modification call Story.update.
        '''
        super(Story, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(Story, self).update(*args, **kwargs)
        self.reload()
    
    def get_tasks(self):
        # import is done here to avoid cyclic references.
        from datamodels.task import Task
        tasks = Task.objects.filter(story=self,
                                    is_active=True).order_by('sequence')
        return tasks

    @classmethod
    def create_todo(cls, project=None, user=None):
        # it may be the case that there exist a regular story with name 'TODO'.
#        probable_todos = Story.objects.filter(project=project,
#                                             title='TODO')
        todo_sprint = Sprint.objects.get(project=project,
                                         sequence=-1)
        data = {'sprint': todo_sprint,
                'project': project,
                'title': 'TODO',
                'created_by': user,
                'updated_by': user
                }
        story = Story(**data)
        story.save()
        story.update(set__sequence=0)
        ProjectMetadata.update_story_metadata(story)

signals.pre_save.connect(Story.pre_save, sender=Story)
signals.post_save.connect(Story.post_save, sender=Story)

