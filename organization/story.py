'''
Created on 19-Aug-2013

@author: someshs
'''

from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.story import Story
from datamodels.organization import Organization
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
import json


class StoryHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('id',),
        'PUT': ('title','sprint', 'priority', 'projectId'),
        'DELETE' : ('id',),
        }
    data = {}
    
    
    def clean_request(self):
        if 'organization' not in self.data.keys():
            self.send_error(404)
        else:
            try:
                org = Organization.get_organization_object(self.data['organization'])
                self.data['organization'] = org
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        
        sequence = self.data['projectId']
        project = self.get_project_object(sequence=sequence,
                                             org=org)
        try:
            sprint = project.get_sprint_object(int(self.data['sprint']))
            [self.data.pop(key) for key in self.data.keys()
             if key not in Story._fields.keys()]
            self.data['project'] = project
            self.data['sprint'] = sprint
            if self.request.method == 'PUT':
                self.data['created_by'] = self.current_user
            self.data['updated_by'] = self.current_user
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            try:
                org = Organization.get_organization_object(organization)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
            return org

    def get_project_object(self, sequence=None, org=None):
        try:
            project = Project.get_project_object(sequence=sequence,
                                          is_active=True,
                                          organization=org)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        story = Story(**self.data)
        try:
            story.save(validate=True, clean=True)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(story.to_json())

    def get_project_stories(self, project_id, organization):
        project = self.get_project_object(sequence=project_id,
                                          org=organization)
        if project and self.current_user in project.members:
            return Project.get_story_list(project)
        else:
            self.send_error(404)

    @authenticated
    def get(self,*args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        story_id = self.get_argument('storyId', None)
        project_id = self.get_argument('projectId', None)
        response = None
        if story_id and not project_id:
            self.send_error(400)
        if project_id and story_id:
            project = self.get_project_object(sequence=project_id,
                                              org=org)
            if project and story_id:
                try:
                    story = Story.objects.get(sequence=int(story_id),
                                              project=project)
                    response = story.to_json()
                except Story.DoesNotExist, error:
                    raise HTTPError(500, **{'reason':self.error_message(error)})
            elif not story_id and project:
                response = json_dumper(Story.objects.filter(project=project))
        else:
            response = json_dumper(Story.objects.filter(is_active=True,
                                    created_by=self.current_user
                                    ).order_by('created_at'))
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        '''TBD'''
        sequence = self.get_argument('id', None)
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project = self.get_project_object(sequence=sequence,
                                          org=org)
        self.write(project.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        story_id = self.get_argument('storyId', None)
        if not story_id:
            self.send_error(404)
        else:
            try:
                story = Story.objects.get(sequence=int(story_id))
                story.update(set__is_active=False)
                response = story.to_json()
            except Story.DoesNotExist, error:
                raise HTTPError(500, **{'reason':self.error_message(error)})
        self.finish(json.dumps(response))


