'''
Created on 23-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project
from datamodels.task import Task
from utils.dumpers import json_dumper


class TaskHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('projectId','taskId'),
        'PUT': ('projectId', 'title','storyId', 'description'),
        'DELETE' : ('projectId','taskId'),
        }
    data = {}
    
    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        if self.request.method == 'PUT':
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        response = None
        if project_id:
            try:
                project = Project.get_project_object(project_id)
                response = project.to_json()
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        response = None
        try:
            project = Project.get_project_object(project_id)
            response = project.to_json()
            self.write(response)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

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
        sequence = self.get_argument('projectId', None)
        try:
            project = Project.get_project_object(sequence)
            project.update(set__active=False)
            self.write(project.to_json())
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})