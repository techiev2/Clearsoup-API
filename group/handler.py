'''
Created on 23-Oct-2013

@author: someshs
'''

import ast
from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.user import User
from datamodels.group import Group
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
from datamodels.permission import ProjectPermission
from requires.settings import PROJECT_PERMISSIONS


class GroupHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE', 'PUT')
    REQUIRED_FIELDS   = {
        'POST': ('name','permissions'),
        'PUT': ('name','permissions'),
        }

    def get_user_object(self, username):
        self.data['members'] = []
        if not username:
            self.send_error(404)
        try:
            user = User.objects.get(username=username)
            self.data['members'].append(user)
        except User.DoesNotExist:
            raise ValidationError('Invalid username ')
        return user


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

    def generate_readable_permission_json(self, group=None):
        permission_dict = {}
        for perm in PROJECT_PERMISSIONS:
            if Group.testBit(group.map,
                             PROJECT_PERMISSIONS.index(perm)):
                permission_dict[perm] = 1
            else:
                permission_dict[perm] = 0
        return permission_dict

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        username = self.get_argument('username', None)
        if not project_id and not username:
            self.send_error(404)
        user = self.get_user_object(username)
        project = self.get_project_object(project_id)
        try:
            permission = ProjectPermission.objects.get(project=project,
                                                       user=user)
            permission_dict = self.generate_readable_permission_json(permission)
            response = {'permission_dict' : permission_dict,
                        'permission_object': permission.to_json()}
            self.write(response)
        except ProjectPermission.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

    @authenticated
    def post(self, *args, **kwargs):
        '''
        
            Modify a group.
            {
            projectId : 1,
            permissions: {'can_edit_story': 1, 'can_delete_story'; 0 ..},
            name: group name,
            project_permalink: project.permalink,
            roles: [a, b, c] send this set of roles always, even if there is
                    no change in the role list. It will help in not checking
                    for a difference. 
            }
        '''
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        name = self.get_argument('name')
        roles = self.get_argument('roles')
        permission_dict = ast.literal_eval(self.get_argument('permissions'))
        self.data.update({'permissions':permission_dict})
        project = None
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
        try:
            group = Group.objects.get(name=name, project=project)
            if roles:
                roles = ast.literal_eval(roles)
                group.update(set__roles=list(roles))
            for key, value in self.data['permissions'].iteritems():
                position = PROJECT_PERMISSIONS.index(key)
                test_bit = Group.testBit(group.map, position)
                if value == 1:
                    if not test_bit:
                        new_map = Group.toggleBit(group.map, position)
                        group.update(set__map=new_map)
                elif value == 0:
                    if test_bit:
                        new_map = Group.toggleBit(group.map, position)
                        group.update(set__map=new_map)
            permission_dict = self.generate_readable_permission_json(group)
            response = {'permission_dict' : permission_dict,
                        'group': group.to_json()}
        except Group.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        self.write(response)

    @authenticated
    def put(self, *args, **kwargs):
        '''
            create a group
            {
            projectId : 1,
            permissions: {'can_edit_story': 1, 'can_delete_story'; 0 ..},
            name: group name,
            project_permalink: project.permalink
            }
        '''
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        name = self.get_argument('name')
        permission_dict = ast.literal_eval(self.get_argument('permissions'))
        self.data['permissions'] = permission_dict
        project = None
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
        try:
            group = Group.objects.get(name=name, project=project)
            raise HTTPError(404, **{'reason': 'Another group with this name already exists'})
        except Group.DoesNotExist:
            group = Group(name=name,
                          project=project,
                          created_by=self.current_user,
                          updated_by=self.current_user)
            group.save()
            map_str = ['0'] * len(PROJECT_PERMISSIONS)
            for key, value in self.data['permissions'].iteritems():
                position = PROJECT_PERMISSIONS.index(key)
                map_str[position] = str(value)
            map_str = "".join(map_str)
            group.update(set__map=int(map_str, 2))
            permission_dict = self.generate_readable_permission_json(group)
            response = {'permission_dict' : permission_dict,
                        'group': group.to_json()}
            self.write(response)
        except Group.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

