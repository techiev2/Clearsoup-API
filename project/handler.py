'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine import ValidationError, Q

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.analytics import ProjectMetadata
from datamodels.project import Project, Sprint
from datamodels.organization import Organization
from datamodels.story import Story
from datamodels.user import User
from datamodels.permission import ProjectPermission
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper


class ProjectHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('projectId',),
        'PUT': ('title','start_date', 'end_date'),
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


    # def get_context(self, context):
    #     """
    #     Returns the user or project context object
    #     """
    #     try:


    @authenticated
    def get(self, *args, **kwargs):
        """
        Get a list of projects by passing in:
        1) projectId - the project sequence number (returns a single project)
        2) owner and project_name - Gets the project in either 
        the user or org context
        3) No params - List all the projects for the current authenticated user
        """
        sequence = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        
        response = {}
        # By Sequence number
        if sequence:
            try:
                project = Project.get_project_object(sequence)
                if self.current_user in project.members:
                    response['project'] = project.to_json()
                    response['project'].update({
                        'current_sprint' : project.get_current_sprint().to_json()
                    })
                else:
                    raise HTTPError(404, **{'reason': "Project Not found."})
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        
        # By permalink
        elif owner and project_name:
            permalink = owner + '/' + project_name
            try:
                project = Project.objects.get(
                            permalink__iexact=permalink,
                            members=self.current_user
                        )
                if not project:
                    raise HTTPError(404)
                
                if not self.current_user in project.members:
                    raise HTTPError(403)
            
                response['project'] = project.to_json()
                response['project'].update({
                    'current_sprint' : project.get_current_sprint().to_json()
                })
            except Project.DoesNotExist:
                raise HTTPError(404)

        # All projects for the current
        else:
            # Check if we are returning a list of projects for
            # the logged in user
            projects = Project.objects(members=self.current_user
                                       ).order_by('created_on')
            response['projects'] = []
            for p in projects:                
                response['projects'].append(p.to_json())
                response['projects'][-1].update({
                    'current_sprint': p.get_current_sprint().to_json()
                })
        
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
                          map=2047,
                          role="Admin")
        p.save()

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        project = Project(**self.data)
        try:
            project.save(validate=True, clean=True)
            self.set_user_permission(project)
            ProjectMetadata.create_project_metadata(project)
            Story.create_todo(project, self.current_user)
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

