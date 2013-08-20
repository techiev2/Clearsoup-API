'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project
from datamodels.permission import ProjectPermission
from datamodels.update import Update
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
        [self.data.pop(key) for key in self.data.keys()
         if key not in Project._fields.keys()]
        for k in ['start_date', 'end_date']:
            self.data[k] = millisecondToDatetime(self.data[k])
        self.data['duration'] = int(self.data['duration'])
        if self.request.method == 'PUT':
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    @classmethod
    def get_project_object(self, sequence):
        try:
            project = Project.objects.get(sequence=sequence)
            project.update(set__active=False)
        except Project.DoesNotExist:
            project = None
        return project

    @authenticated
    def get(self,*args, **kwargs):
        sequence = self.get_argument('id', None)
        response = None
        if sequence:
            try:
                project = Project.get_project_object(sequence)
                response = project.to_json()
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
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
        sequence = self.get_argument('id', None)
        try:
            project = Project.get_project_object(sequence)
            project.update(set__active=False)
            self.write(project.to_json())
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})



class UpdateHandler(BaseHandler):
    """
    Project updates handler
    Since an update is always tied to a project context,
    this is handled within the project    
    """
    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        # 'GET': ('project',),
        'PUT': ('text',),
        'DELETE' : ('id',)
        }

    def get_project(self, project_name):
        try:
            project = Project.objects.get(title__iexact=project_name)
            # project.update(set__active=False)
        except Project.DoesNotExist:
            project = None
        return project

    @authenticated
    @validate_path_arg
    def put(self, project, *args, **kwargs):
        # Get the project object
        # project_id = self.get_argument('project_id', None)
        project = self.get_project(project)
        if not project:
            self.send_error(404)
        # Create a new update
        update = Update()
        update.created_by = self.current_user
        update.project = project
        update.text = self.get_argument('text', None)
        try:
            update.save()
        except Exception:
            raise HTTPError(500, 'Could not save update')

        self.write({
            'status': 200,
            'message': 'Update saved successfully'
            })

    @authenticated
    def get(self, project, *args, **kwargs):
        project = self.get_project(project)
        if not project:
            self.send_error(404)
        # Retrieve updates
        updates = None
        try:
            updates = Update.objects(project=project)
        except Exception:
            raise HTTPError(404)

        if not updates:
            raise HTTPError(404)

        response = json_dumper(updates)
        self.finish(json.dumps(response))

    @authenticated
    def delete(self, *args, **kwargs):
        pass
