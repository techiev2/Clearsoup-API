'''
Created on 06-Aug-2013

@author: someshs
'''

from datetime import datetime, timedelta
import sys
sys.dont_write_bytecode = True

import mongoengine as me
from mongoengine.base import ValidationError
from mongoengine import signals

from utils.dumpers import json_dumper


class Project(me.Document):
    '''
        Basic project fields.
    '''
    
#    organization = me.ReferenceField('Oraganization')
    # these four will come in request data for put
    title = me.StringField(max_length=64, required=True, unique=True)
    start_date = me.DateTimeField(default=datetime.utcnow())
    end_date = me.DateTimeField(default=datetime.utcnow())
    duration = me.IntField() #  sprint duration
    updates = me.ListField()

    # following has to be updated at time of saving object
    sequence = me.IntField()
    sprints = me.ListField()
    members = me.ListField()
    admin = me.ListField()
    active = me.BooleanField(default=True)
    
    # these have to be moved to base model
    created_by = me.ReferenceField('User', required=True)
    updated_by = me.ReferenceField('User', required=True)
    created_at = me.DateTimeField(default=datetime.utcnow())
    updated_at = me.DateTimeField(default=datetime.utcnow())
    deleted_at = me.DateTimeField()
    

    @classmethod
    def post_init(cls, sender, document, **kwargs):
        pass

    def __str__(self):
        return self.title
    
    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)
    
    def clean(self):
        Project.objects.filter(title=self.title).count()
        if Project.objects.filter(title=self.title).count() > 0:
            raise ValidationError('Duplicate project')
        if self.start_date > self.end_date:
            raise ValidationError('start date should be greater than end date.')
    
    @classmethod
    def last_project_id(cls):
        sequence = None
        if Project.objects:
            sequence = list(Project.objects.order_by('sequence'))[-1].sequence
        return sequence
    
    @classmethod
    def pre_save(cls, sender, document, **kwargs):
        '''
        1. check if project already exists,
        2. create id for project
        '''
        last_sequence = cls.last_project_id()
        if last_sequence:
            document.sequence = last_sequence + 1
        else:
            document.sequence = 1
    
    @classmethod
    def post_save(cls, sender, document, **kwargs):
        '''
            1. update sequence value
        '''
        if document.sequence:
            document.update(set__sequence=document.sequence,
                            set__members=[document.created_by],
                            set__admin=[document.created_by])

    def create_sprints(self):
        for (idx, sprint) in enumerate(self.sprints):
            if idx != 0:
                proj_start_date = self.start_date
                sprint_duration = int(self.duration)
                sprint_start_date = proj_start_date + timedelta(
                    days=((idx - 1) * sprint_duration))
                sprint_end_date = sprint_start_date + timedelta(
                    days=sprint_duration)

                (proj_sprint, created) = Sprint.objects.get_or_create(
                                            sequence=idx,
                                            project=self,
                                            start_date=sprint_start_date,
                                            end_date=sprint_end_date)
            else:
                # for backlog
                (proj_sprint, created) = Sprint.objects.get_or_create(
                                            sequence=idx,
                                            project=self)
    def calculate_sprints(self):
        if not self.duration:
            self.duration = 7
        project_duration = (self.end_date - self.start_date).days
        sprints = project_duration / self.duration

        # in case duration is of form 7K + 1, one sprint has to be added
        difference = project_duration - (self.duration * sprints)

        if difference > 0 and difference < 7:
            sprints += 1

        sprint_list = ['Backlog']
        sprint_list.extend(['Sprint ' + str(
                            idx) for idx in range(1, sprints + 1)])
        self.update(set__sprints=sprint_list)
        self.create_sprints()

    def get_current_sprint(self):
        now = datetime.utcnow()
        sprints = Sprint.objects.filter(project=self,
                                       sequence__ne=0,
                                       start_date__lte=now,
                                       end_date__gte=now)
        if len(sprints) == 1:
            curr_sprint = sprints[0]
        elif self.start_date > now:
            curr_sprint = Sprint.objects.get(project=self,
                                            sequence=0)
        else:
            curr_sprint = Sprint.objects.get(project=self,
                                            sequence=(
                                                len(self.sprints)-1))
        return curr_sprint
    
    def save(self, *args, **kwargs):
        '''
            call save only in case of project PUT.
            for any modification call project.update.
        '''
        super(Project, self).save(*args, **kwargs)
        self.calculate_sprints()
        self.reload()
    
    def update(self, *args, **kwargs):
        super(Project, self).update(*args, **kwargs)
        self.reload()


class Sprint(me.Document):

    start_date = me.DateTimeField()
    end_date = me.DateTimeField()
    sequence = me.IntField(required=True, default=0, unique_with='project')
    project = me.ReferenceField('Project')

    def save(self, *args, **kwargs):
        super(Sprint, self).save(*args, **kwargs)

    def update(self, *args, **kwargs):
        super(Sprint, self).update(*args, **kwargs)
        self.reload()

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)


signals.pre_save.connect(Project.pre_save, sender=Project)
signals.post_save.connect(Project.post_save, sender=Project)

signals.post_init.connect(Project.post_init, sender=Project)
