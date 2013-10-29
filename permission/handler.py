'''
Created on 16-Aug-2013

@author: someshs
'''
import ast
import json
from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.user import User
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper
from datamodels.permission import Role
from requires.settings import PROJECT_PERMISSIONS


class PermissionHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('permissions', 'role'),
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


    def generate_readable_permission_json(self, role=None):
        permission_dict = {}
        for perm in PROJECT_PERMISSIONS:
            if Role.testBit(role.map,
                             PROJECT_PERMISSIONS.index(perm)):
                permission_dict[perm] = 1
            else:
                permission_dict[perm] = 0
        return permission_dict

    @authenticated
    def get(self,*args, **kwargs):
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        role = self.get_argument('role')
        project = None
        response = {}
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
        if self.current_user not in project.members:
            raise HTTPError(404, **{'reason': 'Project not found'})
        if not project_id and not role:
            self.send_error(404)
        try:
            permission = Role.objects.get(project=project,
                                                       role=role)
            permission_dict = self.generate_readable_permission_json(permission)
            response = {'permission_dict' : permission_dict,
                        'permission_object': permission.to_json()}
            self.write(response)
        except Role.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

    @authenticated
    def post(self, *args, **kwargs):
        '''
            {
            projectId : 1,
            permissions: {'can_edit_story': 1, 'can_delete_story'; 0 ..},
            role: admin
            project_permalink: somesh/clearsoup
            }
        '''
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        role = self.get_argument('role')
        project = None
        response = {}
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
        if self.current_user not in project.members:
            raise HTTPError(404, **{'reason': 'Project not found'})

        if role == 'admin':
            self.send_error(400)
        else:
            try:
                role = Role.objects.get(role=role, project=project)
                self.data['permissions'] = ast.literal_eval(self.data['permissions'])
                for key, value in self.data['permissions'].iteritems():
                    position = PROJECT_PERMISSIONS.index(key)
                    test_bit = Role.testBit(role.map, position)
                    if value == 1:
                        if not test_bit:
                            new_map = Role.toggleBit(role.map,
                                                     position)
                            role.update(set__map=new_map)
                    elif value == 0:
                        if test_bit:
                            new_map = Role.toggleBit(role.map,
                                                     position)
                            role.update(set__map=new_map)
                permission_dict = self.generate_readable_permission_json(role)
                response = {'permission_dict' : permission_dict,
                            'permission_object': role.to_json()}
                self.write(response)
            except Role.DoesNotExist, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})

    @authenticated
    def delete(self, *args, **kwargs):
        '''
            {
            projectId : 1,
            roles: [admin, developer]
            project_permalink: somesh/clearsoup
            is_delete: true,
            }
        '''
        project_id = self.get_argument('projectId', None)
        owner = self.get_argument('owner', None)
        project_name = self.get_argument('project_name', None)
        project_permalink = self.get_argument('project_pemalink', None)
        roles_to_be_deleted = self.get_argument('roles')
        project = None
        response = {}
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

        if any([x == 'admin' for x in roles_to_be_deleted]):
            self.send_error(500)
        else:
            roles = Role.objects.filter(project=project)
            [role.delete() for role in roles if role.role in roles_to_be_deleted]
            [project.roles.pop(project.roles.index(r)) for r
             in roles_to_be_deleted if r in project.roles]
            response['roles'] = json_dumper(list(Role.objects.filter(project=project)))
            self.finish(json.dumps(response))
