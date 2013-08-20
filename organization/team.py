'''
Created on 16-Aug-2013

@author: someshs
'''

from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.organization import Organization
from datamodels.project import Project
from datamodels.user import User
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
import json


class TeamHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('usernames',),
        'DELETE' : ('usernames',),
        }
    data = {}

    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            try:
                org = Organization.get_organization_object(organization)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
            return org

    def clean_request(self, org):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        
        self.data['members'] = []
        for each in self.data['usernames']:
            try:
                user = User.objects.get(username=each)
                if user and org not in user.belongs_to:
                    raise HTTPError(404, **{'reason': 'User needs to be a member of this Organization'})
                self.data['members'].append(user)
            except User.DoesNotExist:
                raise ValidationError('Invalid username ' + each)

    def get_project_object(self, sequence=None, organization=None):
        try:
            project = Project.get_project_object(sequence=str(sequence),
                                          organization=organization)
            print project
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    @authenticated
    def get(self,*args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project_id = self.get_argument('projectId', None)
        if not project_id:
            self.send_error(404)
        else:
            project = self.get_project_object(project_id, org)
            members = [user for user in project.members]
            self.write(json.dumps(json_dumper(members)))

    @authenticated
    def post(self, *args, **kwargs):
        '''
            send array of usernames which are already in the system.
            usernames = [u1, u2, u3]
        '''
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project_id = self.data.get('projectId', None)
        if not project_id:
            self.send_error(404)
        else:
            self.clean_request(org)
            project = self.get_project_object(project_id, org)
            project.members.extend(self.data['members'])
            project.update(set__members=set(project.members))
            self.write(project.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project_id = kwargs.get_argument('projectId', None)
        if not project_id:
            self.send_error(404)
        else:
            project = self.get_project_object(project_id, org)
            existing_members = project.members
            [existing_members.pop(existing_members.index(each)) for each in 
             self.data['members']]
            project.update(set__members=existing_members)
            self.write(project.to_json())

