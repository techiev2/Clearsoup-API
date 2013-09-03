'''
Created on 23-Aug-2013

@author: someshs
'''
'''
Created on 06-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project
from datamodels.update import Update
from utils.dumpers import json_dumper
from utils.app import slugify

class UpdateHandler(BaseHandler):
    """
    Project updates handler
    Since an update is always tied to a project context,
    this is handled within the project    
    """
    SUPPORTED_METHODS = ('GET', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'GET': ('project_id',),
        'PUT': ('project_id', 'text',),
        'DELETE' : ('id',)
        }

    def get_project(self, project_id):
        try:
            project = Project.objects.get(
                        sequence=project_id,
                        members=self.current_user
                    )
        except Project.DoesNotExist:
            project = None
        return project

    @authenticated
    @validate_path_arg
    def put(self, *args, **kwargs):
        project_id = self.get_argument('project_id', None)
        # Get the project object
        project = self.get_project(project_id)
        if not project:
            self.send_error(404)
        # Create a new update
        update = Update()
        update.created_by = self.current_user
        update.project = project
        update.text = self.get_argument('text', None)
        try:
            update.save()
        except Exception, e:
            print e
            raise HTTPError(500, 'Could not save update')

        self.write({
            'status': 200,
            'message': 'Update saved successfully'
            })

    @authenticated
    def get(self, *args, **kwargs):
        project_id = self.get_argument('project_id', None)
        # Get the project object
        project = self.get_project(project_id)
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
