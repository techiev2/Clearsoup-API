'''
Created on 19-Aug-2013

@author: someshs
'''
from datamodels.permission import OrganizationPermission

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


class OrgMemeberHandler(BaseHandler):
       
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
        self.data['members'] = []
        for each in self.data['usernames']:
            try:
                user = User.objects.get(username=each)
                self.data['members'].append(user)
            except User.DoesNotExist:
                raise HTTPError(404, **{'reason': 'Invalid username ' + each})

    @authenticated
    def get(self,*args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if org not in self.current_user.belongs_to:
            self.send_error(404)
        members = [user.username for user in User.objects if
                   org in user.belongs_to]
        self.write(json.dumps(members))

    def set_user_permission(self, organization=None, user=None):
        p = OrganizationPermission(organization=organization,
                                   user=user,
                                   map=0)
        p.save()

    @authenticated
    def post(self, *args, **kwargs):
        '''
            send array of usernames which are already in the system.
            usernames = [u1, u2, u3]
        '''
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        self.clean_request(org)
        response = {}
        for each in self.data['members']:
            each.belongs_to.append(org)
            each.update(set__belongs_to=each.belongs_to)
            self.set_user_permission(org, each)
        response[org.name] = [u.username for u in self.data['members']]
        self.write(response)

    @authenticated
    def delete(self, *args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        self.clean_request(org)
        existing_members = User.objects.filter(belongs_to__in=org)
        response = {}
        [each.belongs_to.pop(each.belongs_to.index(org))
         for each in self.data['members'] if each in existing_members]
        response[org.name] = [u.username for u in 
                              User.objects.filter(belongs_to__in=org)]
        self.write(response)

