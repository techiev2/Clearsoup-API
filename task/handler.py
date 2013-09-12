'''
Created on 23-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project
from datamodels.story import Story
from datamodels.task import Task
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper


class TaskHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('projectId','taskId'),
        'PUT': ('projectId', 'title','storyId', 'estimated_completion_date', 
                'parentTaskId'),
        'DELETE' : ('projectId','taskId'),
        }
    data = {}
    
    def clean_request(self):
        if self.request.method == 'PUT':
            for k in ['estimated_completion_date',]:
                self.data[k] = millisecondToDatetime(self.data[k])
            self.data['project'] = self.get_project_object(
                                                   self.data['projectId'])
            self.data['story'] = self.get_story_object(
                                               project=self.data['project'],
                                               sequence=self.data['storyId'])
            self.data['parent_task'] = self.get_task_object(
                                        project=self.data['project'],
                                        sequence=self.data['parentTaskId'])
            [self.data.pop(key) for key in self.data.keys()
                if key not in Task._fields.keys()]
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    def get_project_object(self, sequence):
        try:
            project = Project.get_project_object(sequence=sequence)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    def get_story_object(self, project=None, sequence=None):
        try:
            story = Story.objects.get(sequence=sequence, project=project)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return story
    
    def get_task_object(self, project=None, sequence=None):
        task = None
        if sequence:
            try:
                task = Task.objects.get(project=project,sequence=sequence)
            except Task.DoesNotExist:
                pass
        return task

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId',None)
        response = {}
        if project_id:
            project = self.get_project_object(project_id)
            if task_id:
                task = self.get_task_object(project, task_id)
                if not task:
                    raise HTTPError(404, **{'reason': 'Task matching query not found'})
                else:
                    response['task'] = task.to_json()
            else:
                response = json_dumper(Task.objects.filter(project=project
                                       ).order_by('sequence'))
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId',None)
        response = {}
        if project_id:
            project = self.get_project_object(project_id)
            if task_id:
                task = self.get_task_object(project=project, sequence=task_id)
                if 'state' in self.data.keys() and self.data['state']:
                    task.task_state_transition(data=self.data,
                                               user=self.current_user)
                
                # update a task
        self.finish(json.dumps(response))

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        task = Task(**self.data)
        try:
            task.save(validate=True, clean=True)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(task.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId',None)
        response = {}
        if project_id:
            project = self.get_project_object(project_id)
            if task_id:
                task = self.get_task_object(project, task_id)
                if not task:
                    raise HTTPError(404, **{'reason': 'Task matching query not found'})
                else:
                    task.update(set__is_active=False)
                    response['task'] = task.to_json()
        self.finish(response)
