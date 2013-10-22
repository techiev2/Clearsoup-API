'''
Created on 09-Oct-2013

@author: someshs
'''

import sys
from datetime import datetime

import mongoengine as me
from mongoengine import ValidationError
from datamodels.project import Project, Sprint
from utils.dumpers import json_dumper

sys.dont_write_bytecode = True


class ProjectMetadata(me.Document):
    '''
        This data model will store the project meta data in following format:
        
        
        {project_permalink:{sprint: [{story_sequence:[{
                                                        day: 1,
                                                        logged: 3
                                                    },
                                                    {
                                                        day: 2,
                                                        logged: 6
                                                    },]
                                                    
                                    },
                                    .
                                    .
                                    ]
                            },
                            {sprint: []
                            }
        }
    '''
    project = me.ReferenceField('Project', required=True, dbref=True,
                                reverse_delete_rule=me.CASCADE)
    metadata = me.DictField(required=True)
    
    @classmethod
    def which_day(cls, task):
        sprint = task.story.sprint
        diff = (datetime.utcnow() - sprint.start_date).days
        days = 0
        if (diff + 1 ) > task.project.duration:
            days = task.project.duration
        else:
            days = diff + 1
        return days
    
    @classmethod
    def update_task_metadata(cls, task, effort):
        story = task.story
        project = task.story.project
        sprint = story.sprint
        day = cls.which_day(task)
        try:
            project_metadata = ProjectMetadata.objects.get(project=project)
        except ProjectMetadata.DoesNotExist:
            raise ValidationError('No data available')
        day = cls.which_day(task)
        metadata = project_metadata.metadata
        for sprint in metadata[story.project.permalink]:
            if int(sprint) == story.sprint.sequence:
                sprint_dict = metadata[story.project.permalink][sprint]
                story_dict = sprint_dict[str(task.story.sequence)]
                day_work_list = story_dict
                for each in day_work_list:
                    if each['day'] == day:
                        if each['logged']:
                            each['logged'] = int(each['logged']) + int(effort)
                        else:
                            each['logged'] = effort
        project_metadata.update(set__metadata=metadata)

    @classmethod
    def update_story_metadata(cls, story):
        project_metadata = None
        try:
            project_metadata = ProjectMetadata.objects.get(project=story.project)
        except ProjectMetadata.DoesNotExist:
            raise ValidationError('No data available')
        metadata = project_metadata.metadata
        for sprint in metadata[story.project.permalink]:
            if int(sprint) == story.sprint.sequence:
                sprint_dict = metadata[story.project.permalink][sprint]
                sprint_dict.update({str(story.sequence):[]})
                for day in xrange(story.project.duration):
                    sprint_dict[str(story.sequence)].append({'day':int(day) + 1, 'logged': 0})
        project_metadata.update(set__metadata=metadata)

    @classmethod
    def create_project_metadata(cls, project):
        '''
            This method will create the basic metadata dictionary till sprint level.
            After that when each and every story is getting created further 
            dict will be added.
        '''

        permalink = project.permalink
        d = {permalink: {}}
        sprints = Sprint.objects.filter(project=project)
        for sprint in sprints:
            d[permalink].update({str(sprint.sequence):{}})
        
        project_metadata = ProjectMetadata(
                               project=project,
                               metadata=d)
        project_metadata.save()

    def save(self, *args, **kwargs):
        '''
            call save only in case of project PUT.
            for any modification call project.update.
        '''
        super(ProjectMetadata, self).save(*args, **kwargs)
        self.reload()

    def update(self, *args, **kwargs):
        super(ProjectMetadata, self).update(*args, **kwargs)
        self.reload()

    def to_json(self, fields=None, exclude=None):
        return json_dumper(self, fields, exclude)