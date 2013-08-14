'''
Created on 14-Aug-2013

@author: someshs
'''
import sys
from datetime import datetime
from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.organization import Organization
from datamodels.project import Project
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper

sys.dont_write_bytecode = True

class OrgProjectHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS   = {
        'PUT': ('name',),
        }
    data = {}
    
    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            return Organization.get_organization_object(organization)

    def __init__(self, *args, **kwargs):
        super(OrgProjectHandler, self).__init__(*args **kwargs)
    
    @authenticated
    def get(self, *args, **kwargs):
        organization = kwargs.get_argument('organization', None)
        org = self.validate_request(organization)
        response = None
        if not org:
            self.send_error(404)
        else:
            project_id = kwargs.get_argument('projectId', None)
            if not project_id:
                projects = Project.objects.filter(organization=org,
                                              is_active=True)
                response = json_dumper(projects)
            elif project_id:
                project = Project.get_project_object(sequnece=project_id,
                                                         organization=org)
                if not project:
                    self.send_error(404)
                else:
                    response = project.to_json()
            self.write(response)
