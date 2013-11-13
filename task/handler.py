'''
Created on 23-Aug-2013

@author: someshs
'''
import json
import re
from tornado.web import HTTPError
from mongoengine import Q
from mongoengine.errors import ValidationError


from requires.base import BaseHandler, authenticated, validate_path_arg
from datamodels.analytics import ProjectMetadata
from datamodels.user import User
from datamodels.project import Project, Sprint
from datamodels.story import Story
from datamodels.task import Task, TASK_TYPES
from datamodels.team import Team
from datamodels.permission import Role
from datamodels.update import TaskUpdate
from utils.app import millisecondToDatetime
from utils.dumpers import json_dumper
from requires.settings import PROJECT_PERMISSIONS


class TaskHandler(BaseHandler):
    
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('taskId',),
        'PUT': ('projectId', 'title', 'estimated_completion_date', 
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
            if 'estimated_effort' in self.data.keys() and\
             self.data['estimated_effort']:
                pat = "^-?[0-9]+$"
                val = re.findall(pat , self.data['estimated_effort'])
                if val:
                    self.data['estimated_effort'] = int(val[0])
                else:
                    raise HTTPError(404, **{'reason': 'Efforts should be only in integers.'})
            else:
                self.data.pop('estimated_effort')
            self.data['project'] = self.get_project_object(
                                                   self.data['projectId'])
            if 'assigned_to' in self.data.keys() and\
                self.data['assigned_to']:
                try:
                    user = User.objects.get(Q(username=self.data['assigned_to'])|Q(
                                            email=self.data['assigned_to']))
                    if user not in self.data['project'].members:
                        raise HTTPError(404, **{'reason': 'User not in project.'})
                except User.DoesNotExist:
                    raise HTTPError(404, **{'reason': 'User not in project.'})
                self.data['assigned_to'] = user
                self.data['current_action'] = 'start'
                self.data['current_state'] = 'Assigned'
            else:
                self.data.pop('assigned_to')
                self.data['current_action'] = 'assign'
                self.data['current_state'] = 'New'
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
        if Role.testBit(permission.map,
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
                    msg = 'Invalid task sequences'
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
                    response['events'] = task.next_events()
                    response['current'] = task._state_machine.current
                    response['task'] = task.to_json()
                    response['task_type'] = TASK_TYPES
            else:
                query = {
                    'project': project,
                    'is_active': True
                }
                # If sprint is set, get the tasks only for that sprint
                sprint_number = self.get_argument('sprint', None)
                sprint_metadata = {}
                if sprint_number:
                    # Get the sprint
                    sprint = Sprint.objects.get(project=project,
                                                sequence=int(sprint_number))
                    query['story__in'] = sprint.get_stories()
                    
                    pm = ProjectMetadata.objects.filter(project=project
                                                ).exclude('project')
                    if pm:
                        sprint_metadata = pm[0].metadata[project.permalink][str(sprint_number)]
                    
                response['task'] = json_dumper(list(
                                    Task.objects.filter(**query).exclude('project','story')
                                    .order_by('sequence')
                                ))
                response['metadata'] = sprint_metadata
        self.finish(json.dumps(response))

    def validate_post_data(self, data, task):
        '''
            TB made generic.
        '''
        if not data:
            self.send_error(404)
        user = None
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            raise HTTPError(404, **{'reason': 'User Not Found'})
        if user not in task.project.members:
            raise HTTPError(404, **{'reason': 'User Not Found'})
        self.data['username'] = user
        pat = "^-?[0-9]+$"
        if 'logged_effort' in data.keys() and data['logged_effort']:
            val = re.findall(pat , data['logged_effort'])
            if not val:
                raise HTTPError(403, reason='Efforts should be only in integers')
            
        if 'estimated_effort' in data.keys() and data['estimated_effort']:
            val = re.findall(pat , data['estimated_effort'])
            if not val:
                raise HTTPError(403, **{'reason': 'Efforts should be only in integers.'})
        
        if (task.created_by == self.current_user) or (
          self.current_user in task.project.admin):
            pass
        elif task.assigned_to and (task.assigned_to != self.current_user):
            raise ValidationError('You were not assigned this task')

    @authenticated
    def post(self, *args, **kwargs):
        task_id = self.get_argument('taskId',None)
        project_id = self.get_argument('projectId', None)
        project_permalink = self.get_argument('project_permalink', None)
        response = {}
        project = None
        if project_id:
            project = self.get_project_object(project_id=project_id,
                                              permalink=None)
        elif project_permalink:
            project = self.get_project_object(project_id=None,
                                              permalink=project_permalink)
        task = self.get_task_object(project=project, sequence=task_id)
        if 'event' in self.data.keys() and self.data['event']:
            try:
                self.validate_post_data(self.data, task)
                task.task_state_transition(data=self.data,
                                       user=self.current_user)
            except ValidationError, error:
                raise HTTPError(403, **{'reason':self.error_message(error)})
        if self.data['logged_effort']:
            if not task.logged_effort:
                logged_effort = int(self.data['logged_effort'])
            else:
                logged_effort = task.logged_effort + int(self.data['logged_effort'])
            task.update(set__logged_effort=logged_effort)
            ProjectMetadata.update_task_metadata(task, self.data['logged_effort'])
        if 'estimated_effort' in self.data.keys() and self.data['estimated_effort']:
            estimated_effort = int(self.data['estimated_effort'])
            task.update(set__estimated_effort=estimated_effort)
        response['events'] = task.next_events()
        response['current'] = task._state_machine.current
        response['task'] = task.to_json()
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
            team = None
            try:
                team = Team.objects.get(project=project,
                                                       user=self.current_user)
            except Team.DoesNotExist:
                msg = 'Not authorized to delete tasks of this project'
                raise HTTPError(500, **{'reason':msg})
            if self.check_permission(team.role):
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


class TaskCommentHandler(BaseHandler):
    '''
        taskId is parent task id.
    '''

    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'GET': ('taskId', ),
        'POST': ('projectId','taskId', 'text'),
        'PUT': ('projectId', 'taskId','text'),
        'DELETE' : ('taskCommentId',),
        }
    data = {}
    
    def clean_request(self):
        if self.request.method == 'PUT':
            self.data['project'] = self.get_project_object(
                                                   self.data['projectId'])
            self.data['task'] = self.get_task_object(self.data['project'],
                                                       self.data['taskId'])
            [self.data.pop(key) for key in self.data.keys()
                if key not in TaskUpdate._fields.keys()]
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

    def get_task_object(self, project=None, sequence=None):
        task = None
        if sequence:
            try:
                task = Task.objects.get(project=project,sequence=sequence,
                                        is_active=True)
            except Task.DoesNotExist:
                pass
        return task

    @authenticated
    def get(self,*args, **kwargs):
        '''
            taskId will be that of a parent task.
            This handler will return comments of a task which is always tied
            up to a parent task.
        '''
        project_id = self.get_argument('projectId', None)
        task_id = self.get_argument('taskId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project = None
        if project_id:
            project = self.get_valid_project(project_id)
        elif owner and project_name:
            permalink = owner + '/' + project_name
            project = self.get_project_object(project_id=None,
                                          permalink=permalink)
        else:
            self.send_error(400)
        response = {}
        task = self.get_task_object(project, task_id)
        if not task:
            raise HTTPError(404, **{'reason': 'Task not found'})
        else:
            response['task'] = task.to_json()
            response['task_type'] = TASK_TYPES
            response['task_comments'] = json_dumper(
                                list(TaskUpdate.objects.filter(task=task,
                                          is_active=True).order_by('-id')))
        self.finish(json.dumps(response))

    @authenticated
    def post(self, *args, **kwargs):
        #TBD
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
        task_update = TaskUpdate(**self.data)
        try:
            task_update.save(validate=True, clean=True)
            task_update.reload()
        except ValidationError, error:
            raise HTTPError(500, **{'reason':self.error_message(error)})
        self.write(task_update.to_json())

    def check_permission(self, permission):
        permission_flag = False
        if Role.testBit(permission.map,
                             PROJECT_PERMISSIONS.index('can_delete_task')):
            permission_flag = True
        return permission_flag

    @authenticated
    def delete(self, *args, **kwargs):
        '''
        In case of comments and update deletion will be a single operation not
        bulk.
        '''
        
        project_id = self.get_argument('projectId', None)
        project_permalink = self.get_argument('project_permalink', None)
        taskCommentId = self.get_arguments('taskCommentId', None)
        response = {}
        project = None
        if not project_id or not project_permalink:
            self.send_error(404)
        project = self.get_project_object(project_id=project_id,
                                              permalink=project_permalink)
        if taskCommentId:
            team = None
            try:
                team = Team.objects.get(project=project,
                                                       user=self.current_user)
            except Team.DoesNotExist:
                msg = 'Not authorized to delete comments.'
                raise HTTPError(500, **{'reason':msg})
            if self.check_permission(team.role):
                try:
                    task_update = TaskUpdate.objects.get(id=taskCommentId,
                                              is_active=True)
                    task_update.update(set__is_active=False)
                except TaskUpdate.DoesNotExist, error:
                    raise HTTPError(500, **{'reason':self.error_message(error)})
                response = {'message': 'Successfully deleted.',
                            'status': 200}
            else:
                msg = 'Not authorized to delete comments.'
                raise HTTPError(500, **{'reason':msg})
        self.finish(json.dumps(response))

