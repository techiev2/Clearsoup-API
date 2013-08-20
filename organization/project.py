'''
Created on 14-Aug-2013

@author: someshs
'''
import sys
from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.organization import Organization
from datamodels.project import Project
from datamodels.permission import ProjectPermission
from mongoengine.errors import ValidationError
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper
import json

sys.dont_write_bytecode = True

class OrgProjectHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE', 'PUT')
    REQUIRED_FIELDS = {'PUT': ('title',)}
    data = {}

    def clean_request(self, organization):
        if not organization:
            self.send_error(404)
        else:
            try:
                org = Organization.get_organization_object(organization)
                self.data['organization'] = org
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        
        [self.data.pop(key) for key in self.data.keys()
         if key not in Project._fields.keys()]
        for k in ['start_date', 'end_date']:
            self.data[k] = millisecondToDatetime(self.data[k])
        self.data['duration'] = int(self.data['duration'])
        if self.request.method == 'PUT':
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            try:
                org = Organization.get_organization_object(organization)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
            return org

    def set_user_permission(self, project):
        p = ProjectPermission(project=project,
                          user=self.current_user,
                          map=2047)
        p.save()

    @authenticated
    def get(self, *args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        response = None
        project_id = self.get_argument('projectId', None)
        if not project_id:
            projects = Project.objects.filter(organization=org,
                                          is_active=True)
            response = json_dumper(projects)
        elif project_id:
            try:
                project = Project.get_project_object(sequence=project_id,
                                                     organization=org)
                response = project.to_json()
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        if not self._headers_written:
            self.write(json.dumps(response))
    
    @authenticated
    def put (self, *args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        self.clean_request(organization)
        project = Project(**self.data)
        try:
            project.save(validate=True, clean=True)
            self.set_user_permission(project)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        
        if not self._headers_written:
            self.write(project.to_json())

