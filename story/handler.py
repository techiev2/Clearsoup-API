'''
Created on 07-Aug-2013

@author: someshs
'''

from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.analytics import ProjectMetadata
from datamodels.project import Project
from datamodels.story import Story
from datamodels.task import Task, TASK_TYPES
from datamodels.permission import Role
from datamodels.team import Team
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
import json

from requires.settings import PROJECT_PERMISSIONS


class StoryHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'PUT': ('title','sprint', 'priority', 'projectId'),
        'DELETE': ('stories',)
        }
    data = {}
    
    
    def clean_request(self):
        '''
            function to remove additional data key send in request.
            e.g token
            
            Besides above, it also cleans the date-time values and duration
        '''
        
        sequence = self.data['projectId']
        project =self.get_valid_project(project_id=sequence)
        if not project:
            self.send_error(400)
        else:
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

    def get_valid_project(self, project_id=None, permalink=None):
        if not project_id and not permalink:
            self.send_error(404)
        if project_id:
            try:
                project = Project.get_project_object(sequence=project_id)
                if self.current_user not in project.members:
                    self.send_error(404)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        elif permalink:
            try:
                project = Project.objects.get(
                            permalink__iexact=permalink,
                        )
                if not self.current_user in project.members:
                    raise HTTPError(403)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    def check_permission(self, project, value):
        team = None
        try:
            team = Team.objects.get(project=project,
                                       user=self.current_user)
            permission_flag = False
            if Role.testBit(team.role.map,
                                 PROJECT_PERMISSIONS.index(value)):
                permission_flag = True
            return permission_flag
        except Team.DoesNotExist:
            msg = 'Not permitted to perform this action'
            raise HTTPError(500, **{'reason':msg})

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        if self.check_permission(self.data['project'], value='can_add_story'):
            story = Story(**self.data)
            try:
                story.save(validate=True, clean=True)
                ProjectMetadata.update_story_metadata(story)
            except ValidationError, error:
                raise HTTPError(500, **{'reason':self.error_message(error)})
            self.write(story.to_json())
        else:
            msg = 'Not permitted to create story for this project'
            raise HTTPError(500, **{'reason':msg})


    def get_project_stories(self, project_id):
        project = self.get_valid_project(project_id=project_id)
        if project and self.current_user in project.members:
            return Project.get_story_list(project)
        else:
            self.send_error(404)

    @authenticated
    def get(self,*args, **kwargs):
        story_id = self.get_argument('storyId', None)
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
#        is_pmo = self.get_argument('is_pmo', False)
        response = {}
        if project_id:
            project = self.get_valid_project(project_id)
        elif owner and project_name:
            permalink = owner + '/' + project_name
            project = self.get_valid_project(project_id, permalink)
        else:
            self.send_error(400)
        if project and story_id:
            try:
                story = Story.objects.get(sequence=int(story_id),
                                              project=project,
                                              is_active=True)
                response['story'] = story.to_json()
                response['tasks'] = json_dumper(story.get_tasks())
                response['task_type'] = TASK_TYPES
            except Story.DoesNotExist, error:
                raise HTTPError(500, **{'reason':self.error_message(error)})
        elif not story_id and project:
                response = json_dumper(Story.objects.filter(project=project
                                    ).order_by('-created_at'))
        else:
            response = json_dumper(Story.objects.filter(is_active=True,
                                    created_by=self.current_user
                                    ).order_by('-created_at'))
        self.finish(json.dumps(response))

    def validate_stories(self, project=None, stories=None):
        '''
        This method validates the stories which are send from web to move to
        another sprint or delete
        '''
        flag = False
        if stories:
            id = 0
            for id, story in enumerate(stories):
                try:
                    Story.objects.get(sequence=int(story),
                                      project=project)
                except Story.DoesNotExist:
                    msg = 'Invalid story sequences'
                    raise HTTPError(500, **{'reason':msg})
            if id == len(stories) - 1: flag = True
        return flag 

    @authenticated
    def post(self, *args, **kwargs):
        story_id = self.get_argument('storyId', None)
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        stories = self.get_arguments('stories', []) # in case of deletion
        story = None
        project = None
        self.clean_request()
        
        if project_id:
            project = self.get_valid_project(project_id)
        elif owner and project_name:
            permalink = owner + '/' + project_name
            project = self.get_valid_project(project_id, permalink)
        elif project_permalink:
            project = self.get_valid_project(project_id=None,
                                             permalink=project_permalink)
        else:
            self.send_error(400)
        if self.check_permission(project, 'can_edit_story'):
            if project and story_id:
                try:
                    story = Story.objects.get(sequence=int(story_id),
                                                  project=project)
                    temp_data = {'set__'+field: self.data[field] for field 
                                     in Story._fields.keys() 
                                     if field in self.data.keys()}
                    temp_data.update({'set__updated_by': self.current_user})
                    story.update(**temp_data)
                except Story.DoesNotExist, error:
                    raise HTTPError(500, **{'reason':self.error_message(error)})
                self.write(story.to_json())
            elif stories:
                if self.validate_stories(stories=stories, project=project):
                    for story in stories:
                        try:
                            story = Story.objects.get(sequence=int(story),
                                                      project=project)
                            old_sprint = story.sprint
                            story.update(set__sprint=self.data['sprint'])
                            story.update_sprint_metadata(old_sprint=old_sprint)
                        except Story.DoesNotExist, error:
                            raise HTTPError(500, **{'reason':self.error_message(error)})
                    response = {'message': 'Successfully moved to sprint %s.' % str(
                                                    self.data['sprint'].sequence),
                                'status': 200}
                self.write(response)
            else:
                self.send_error(404)
        else:
            msg = 'Not permitted to modify story for this project'
            raise HTTPError(500, **{'reason':msg})

    @authenticated
    def delete(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        project_permalink = self.get_argument('project_permalink', None)
        stories = self.get_arguments('stories', None)
        if project_id:
            project = self.get_valid_project(project_id)
        elif project_permalink:
            project = self.get_valid_project(project_id, project_permalink)
        if not stories and not project:
            self.send_error(404)
        else:
            if self.check_permission(project, value='can_delete_story'):
                if self.validate_stories(project=project, stories=stories):
                    for story in stories:
                        try:
                            story = Story.objects.get(sequence=int(story),
                                                      project=project,
                                                      is_active=True)
                            story.update(set__is_active=False)
                            tasks  = list(Task.objects.filter(story=story,
                                                project=project,
                                                is_active=True))
                            [task.update(set__is_active=False) for task
                             in tasks]
                        except Story.DoesNotExist, error:
                            raise HTTPError(500, **{'reason':self.error_message(error)})
                    response = {'message': 'Successfully deleted.',
                                'status': 200}
            else:
                msg = 'Not permitted to delete stories of this project'
                raise HTTPError(500, **{'reason':msg})
        self.finish(json.dumps(response))

