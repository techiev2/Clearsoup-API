'''
Created on 21-Aug-2013

@author: someshs
'''

'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated
from datamodels.project import Project, Sprint
from utils.dumpers import json_dumper


class SprintHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'PUT')
    REQUIRED_FIELDS   = {
        'PUT': ('projectId','sprints'),
        'GET': ('projectId',)
        }
    data = {}
    
    def get_valid_project(self, project_id):
        if not project_id:
            self.send_error(404)
        try:
            project = Project.get_project_object(project_id)
            if self.current_user not in project.members:
                self.send_error(404)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        sprint_sequence = self.get_argument('sprint',None)
        response = {}
        project = self.get_valid_project(project_id)
        if not sprint_sequence:
            sprints = list(Sprint.objects.filter(project=project))
            response['sprints'] = json_dumper(sprints)
        elif sprint_sequence:
            try:
                sprint = project.get_sprint_object(sprint_sequence)
                response['sprint'] = sprint.to_json()
                response['stories'] = json_dumper(list(sprint.get_stories()))
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        response['project'] = project.to_json()
        self.finish(json.dumps(response))

    @authenticated
    def put(self, *args, **kwargs):
        project_id = self.data.get('projectId', None)
        number_of_sprints = self.data.get('sprints', None)
        project = self.get_valid_project(project_id)
        if self.current_user != project.admin:
            self.send_error(404)
        response = {}
        for each in xrange(number_of_sprints):
            try:
                sprint = project.add_sprint(self.current_user)
                response['Sprint :' + str(sprint.sequence)] = sprint.to_json()
            except ValidationError, error:
                raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(response)

