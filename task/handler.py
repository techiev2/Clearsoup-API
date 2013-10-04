'''
Created on 23-Aug-2013

@author: someshs
'''
import json
from tornado.web import HTTPError
from mongoengine.errors import ValidationError

from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.project import Project, Sprint
from datamodels.story import Story
from datamodels.task import Task
from datamodels.permission import ProjectPermission
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper
from requires.settings import PROJECT_PERMISSIONS


class TaskHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('projectId','taskId'),
        'PUT': ('projectId', 'title','storyId', 'estimated_completion_date', 
                'parentTaskId'),
        'DELETE' : ('tasks',),
        }
    data = {}
    
    def clean_request(self):
        if self.request.method == 'PUT':
            if 'estimated_completion_date' in self.data.keys() and\
             self.data['estimated_completion_date']:
                for k in ['estimated_completion_date',]:
                    self.data[k] = millisecondToDatetime(self.data[k])
            else:
                self.data.pop('estimated_completion_date')
            self.data['project'] = self.get_project_object(
                                                   self.data['projectId'])
            self.data['story'] = self.get_story_object(
                                               project=self.data['project'],
                                               sequence=self.data['storyId'])
            self.data['parent_task'] = self.get_task_object(
                                        project=self.data['project'],
                                        sequence=self.data['parentTaskId'])
            [self.data.pop(key) for key in self.data.keys()
                if key not in Task._fields.keys()]
            self.data['created_by'] = self.current_user
        self.data['updated_by'] = self.current_user

    def get_project_object(self, project_id=None, permalink=None):
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

    def get_story_object(self, project=None, sequence=None):
        try:
            story = Story.objects.get(sequence=sequence, project=project)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return story
    
    def get_task_object(self, project=None, sequence=None):
        task = None
        if sequence:
            try:
                task = Task.objects.get(project=project,sequence=sequence,
                                        is_active=True)
            except Task.DoesNotExist:
                pass
        return task

    def check_permission(self, permission):
        permission_flag = False
        if ProjectPermission.testBit(permission.map,
                             PROJECT_PERMISSIONS.index('can_delete_task')):
            permission_flag = True
        return permission_flag

    def validate_tasks(self, project=None, tasks=None):
        '''
        This method validates the tasks which are send from web to delete
        '''
        flag = False
        if tasks:
            id = 0
            for id, task in enumerate(tasks):
                try:
                    Task.objects.get(sequence=int(task),
                                      project=project)
                except Task.DoesNotExist:
                    msg = 'Task story sequences'
                    raise HTTPError(500, **{'reason':msg})
            if id == len(tasks) - 1: flag = True
        return flag 

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId',None)
        response = {}
        if project_id:
            project = self.get_project_object(project_id)
            if task_id:
                task = self.get_task_object(project, task_id)
                if not task:
                    raise HTTPError(404, **{'reason': 'Task not found'})
                else:
                    response['task'] = task.to_json()
            else:
                query = {
                    'project': project,
                    'is_active': True,
                }
                # If sprint is set, get the tasks only for that sprint
                sprint_number = self.get_argument('sprint', None)
                if sprint_number:
                    # Get the sprint
                    sprint = Sprint.objects.get(project=project,
                                                sequence=int(sprint_number))
                    query['story__in'] = sprint.get_stories()

                response['task'] = json_dumper(list(
                                    Task.objects.filter(**query).exclude('project','story')
                                    .order_by('sequence')
                                ))
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId',None)
        response = {}
        if project_id:
            project = self.get_project_object(project_id)
            if task_id:
                task = self.get_task_object(project=project, sequence=task_id)
                if 'state' in self.data.keys() and self.data['state']:
                    task.task_state_transition(data=self.data,
                                               user=self.current_user)
                
                # update a task
        self.finish(json.dumps(response))

    @authenticated
    def put(self, *args, **kwargs):
        self.clean_request()
        task = Task(**self.data)
        try:
            task.save(validate=True, clean=True)
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(task.to_json())

    @authenticated
    def delete(self, *args, **kwargs):
        project_id = self.get_argument('projectId', None)
        project_permalink = self.get_argument('project_permalink', None)
        tasks = self.get_arguments('tasks', None)
        response = {}
        project = None
        if project_id:
            project = self.get_project_object(project_id=project_id,
                                              permalink=None)
        elif project_permalink:
            project = self.get_project_object(project_id=None,
                                              permalink=project_permalink)
        if tasks:
            permission = None
            try:
                permission = ProjectPermission.objects.get(project=project,
                                                       user=self.current_user)
            except ProjectPermission.DoesNotExist:
                msg = 'Not authorized to delete tasks of this project'
                raise HTTPError(500, **{'reason':msg})
            if self.check_permission(permission):
                if self.validate_tasks(project=project, tasks=tasks):
                    for task in tasks:
                        try:
                            task = Task.objects.get(sequence=int(task),
                                                      project=project,
                                                      is_active=True)
                            task.update(set__is_active=False)
                        except Task.DoesNotExist, error:
                            raise HTTPError(500, **{'reason':self.error_message(error)})
                    response = {'message': 'Successfully deleted.',
                                'status': 200}
            else:
                msg = 'Not authorized to delete task of this project'
                raise HTTPError(500, **{'reason':msg})
        self.finish(json.dumps(response))

