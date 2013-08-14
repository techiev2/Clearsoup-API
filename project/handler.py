'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.organization import Organization
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper


class ProjectHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('id',),
        'PUT': ('title','start_date', 'end_date', 'duration'),
        'DELETE' : ('id',),
        }
    data = {}
    
    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        if 'organization' in self.data.keys():
            org = Organization.get_organization_object(self.data['organization'])
            if not org:
                self.send_error(404)
            else:
                self.data['organization'] = org
        [self.data.pop(key) for key in self.data.keys()
         if key not in Project._fields.keys()]
        for k in ['start_date', 'end_date']:
            self.data[k] = millisecondToDatetime(self.data[k])
        self.data['duration'] = int(self.data['duration'])
        if self.request.method == 'PUT':
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    @authenticated
    def get(self,*args, **kwargs):
        sequence = self.get_argument('id', None)
        response = None
        if sequence:
            project = Project.get_project_object(sequence)
            if not project:
                self.send_error(404)
            else:
                response = project.to_json()
        else:
            # Check if we are returning a list of projects for
            # the logged in user
            #response = json_dumper(Project.objects(active=True))
            projects = [p for p in Project.objects.all() if self.current_user in
                        p.members]
            response = json_dumper(projects)
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        """TBD"""
        sequence = self.get_argument('id', None)
        response = None
        project = Project.get_project_object(sequence)
        if not project:
            self.send_error(404)
        else:
            response = project.to_json()
        self.write(response)

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        project = Project(**self.data)
        try:
            project.save(validate=True, clean=True)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(project.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        sequence = self.get_argument('id', None)
        project = Project.get_project_object(sequence)
        if not project:
            self.send_error(404)
        else:
            project.update(set__active=False)
            self.write(project.to_json())

