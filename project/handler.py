'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project
from datamodels.permission import ProjectPermission
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper


class ProjectHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('projectId',),
        'PUT': ('title','start_date', 'end_date', 'duration'),
        'DELETE' : ('projectId',),
        }
    data = {}
    
    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        [self.data.pop(key) for key in self.data.keys()
         if key not in Project._fields.keys()]
        for k in ['start_date', 'end_date']:
            self.data[k] = millisecondToDatetime(self.data[k])
        self.data['duration'] = int(self.data['duration'])
        if self.request.method == 'PUT':
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    @authenticated
    def get(self, *args, **kwargs):
        sequence = self.get_argument('projectId', None)
        response = {}
        response['project'] = []
        if sequence:
            try:
                project = Project.get_project_object(sequence)
                if self.current_user in project.members:
                    response['project'].append(project.to_json())
                    response['project'][0].update(
                           {'current_sprint' : project.get_current_sprint().to_json()})
                else:
                    raise HTTPError(404, **{'reason': "Project Not found."})
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        else:
            # Check if we are returning a list of projects for
            # the logged in user
            #response = json_dumper(Project.objects(active=True))
            for p in Project.objects.all():
                if self.current_user in p.members:
                    index = len(response['project'])
                    response['project'].append(p.to_json())
                    response['project'][index].update(
                                   {'current_sprint': p.get_current_sprint().to_json()})
            # projects = [p for p in Project.objects.all() if self.current_user in
            #             p.members]
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        """TBD"""
        sequence = self.get_argument('projectId', None)
        response = None
        try:
            project = Project.get_project_object(sequence)
            response = project.to_json()
            self.write(response)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

    def set_user_permission(self, project):
        p = ProjectPermission(project=project,
                          user=self.current_user,
                          map=2047)
        p.save()

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        project = Project(**self.data)
        try:
            project.save(validate=True, clean=True)
            self.set_user_permission(project)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(project.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        sequence = self.get_argument('projectId', None)
        try:
            project = Project.get_project_object(sequence)
            project.update(set__active=False)
            self.write(project.to_json())
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

