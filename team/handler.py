'''
Created on 16-Aug-2013

@author: someshs
'''

from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.user import User
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
from datamodels.permission import ProjectPermission
import json

class TeamHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS = {
        'POST': ('usernames', 'projectId'),
        'DELETE' : ('usernames', 'projectId'),
        }
    data = {}

    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''

        self.data['members'] = []
        for each in self.data['usernames']:
            try:
                user = User.objects.get(username=each)
                self.data['members'].append(user)
            except User.DoesNotExist:
                raise ValidationError('Invalid username ' + each)

    def get_project_object(self, sequence):
        try:
            project = Project.get_project_object(sequence=sequence)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        project = self.get_project_object(project_id)
        members = [user for user in project.members]
        self.write(json.dumps(json_dumper(members)))

    @authenticated
    def post(self, *args, **kwargs):
        '''
            send array of usernames which are already in the system.
            usernames = [u1, u2, u3]
        '''
        sequence = self.get_argument('projectId', None) 
        project = self.get_project_object(sequence)
        self.clean_request()
        for each in self.data['members']:
            ProjectPermission.objects.create(user=each, project=project)
        project.members.extend(self.data['members'])
        project.update(set__members=set(project.members))
        self.write(project.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        sequence = self.get_argument('projectId', None)
        project = self.get_project_object(sequence)
        self.clean_request()
        existing_members = project.members
        [ProjectPermission.objects.filter(user=each,project=project).delete()
         for each in self.data['members']]
        [existing_members.pop(existing_members.index(each)) for each in 
         self.data['members']]
        project.update(set__members=existing_members)
        self.write(project.to_json())

