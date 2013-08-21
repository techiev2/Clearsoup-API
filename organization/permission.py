'''
Created on 16-Aug-2013

@author: someshs
'''


from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.project import Project
from datamodels.user import User
from mongoengine.errors import ValidationError
from datamodels.permission import ProjectPermission, OrganizationPermission
from datamodels.organization import Organization
from requires.settings import PROJECT_PERMISSIONS, ORGANIZATION_PERMISSIONS


class ProjectPermissionHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('permissions', 'projectId', 'username'),
        }

    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            try:
                org = Organization.get_organization_object(organization)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
            return org

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

    def get_project_object(self, sequence=None, organization=None):
        try:
            project = Project.get_project_object(sequence=sequence,
                                                 organization=organization)
        except ValidationError, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})
        return project

    def generate_readable_permission_json(self, permission=None):
        permission_dict = {}
        for perm in PROJECT_PERMISSIONS:
            if ProjectPermission.testBit(permission.map,
                             PROJECT_PERMISSIONS.index(perm)):
                permission_dict[perm] = 1
            else:
                permission_dict[perm] = 0
        return permission_dict

    @authenticated
    def get(self,*args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project_id = self.get_argument('projectId', None)
        username = self.get_argument('username', None)
        if not project_id and not username:
            self.send_error(404)
        user = self.get_user_object(username)
        if org not in user.belongs_to:
            self.send_error(404)
        project = self.get_project_object(project_id, org)
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
            {
            projectId : 1,
            permissions: {'can_edit_story': 1, 'can_delete_story'; 0 ..},
            username: somesh
            }
        '''
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        project_id = self.data.get('projectId', None)
        username = self.data.get('username', None)
        if not username or not project_id:
            self.send_error(404)
        user = self.get_user_object(username)
        if org not in user.belongs_to:
            self.send_error(404)
        project = self.get_project_object(project_id, org)
        try:
            permission = ProjectPermission.objects.get(user=user,
                                                       project=project)
            for key, value in self.data['permissions'].iteritems():
                position = PROJECT_PERMISSIONS.index(key)
                test_bit = ProjectPermission.testBit(permission.map,
                                                         position)
                if value == 1:
                    if not test_bit:
                        new_map = ProjectPermission.toggleBit(permission.map,
                                                 position)
                        permission.update(set__map=new_map)
                elif value == 0:
                    if test_bit:
                        new_map = ProjectPermission.toggleBit(permission.map,
                                                 position)
                        permission.update(set__map=new_map)
            permission_dict = self.generate_readable_permission_json(permission)
            response = {'permission_dict' : permission_dict,
                        'permission_object': permission.to_json()}
            self.write(response)
        except ProjectPermission.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})


class OrgPermissionHandler(BaseHandler):
       
    SUPPORTED_METHODS = ('GET', 'POST', 'DELETE')
    REQUIRED_FIELDS   = {
        'POST': ('permissions', 'projectId', 'username'),
        }

    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            try:
                org = Organization.get_organization_object(organization)
            except ValidationError, error:
                raise HTTPError(404, **{'reason': self.error_message(error)})
            return org

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


    def generate_readable_permission_json(self, permission=None):
        permission_dict = {}
        for perm in ORGANIZATION_PERMISSIONS:
            if OrganizationPermission.testBit(permission.map,
                             ORGANIZATION_PERMISSIONS.index(perm)):
                permission_dict[perm] = 1
            else:
                permission_dict[perm] = 0
        return permission_dict

    @authenticated
    def get(self,*args, **kwargs):
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        username = self.get_argument('username', None)
        if not username:
            self.send_error(404)
        user = self.get_user_object(username)
        if org not in user.belongs_to:
            self.send_error(404)
        try:
            permission = OrganizationPermission.objects.get(organization=org,
                                                       user=user)
            permission_dict = self.generate_readable_permission_json(permission)
            response = {'permission_dict' : permission_dict,
                        'permission_object': permission.to_json()}
            self.write(response)
        except OrganizationPermission.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

    @authenticated
    def post(self, *args, **kwargs):
        '''
            {
            projectId : 1,
            permissions: {'can_edit_story': 1, 'can_delete_story'; 0 ..},
            username: somesh
            }
        '''
        organization = kwargs.get('organization', None)
        org = self.validate_request(organization)
        username = self.data.get('username', None)
        if not username:
            self.send_error(404)
        user = self.get_user_object(username)
        if org not in user.belongs_to:
            self.send_error(404)
        try:
            permission = OrganizationPermission.objects.get(user=user,
                                                    organization=organization)
            for key, value in self.data['permissions'].iteritems():
                position = ORGANIZATION_PERMISSIONS.index(key)
                test_bit = OrganizationPermission.testBit(permission.map,
                                                         position)
                if value == 1:
                    if not test_bit:
                        new_map = OrganizationPermission.toggleBit(
                                               permission.map,
                                               position)
                        permission.update(set__map=new_map)
                elif value == 0:
                    if test_bit:
                        new_map = OrganizationPermission.toggleBit(permission.map,
                                                 position)
                        permission.update(set__map=new_map)
            permission_dict = self.generate_readable_permission_json(permission)
            response = {'permission_dict' : permission_dict,
                        'permission_object': permission.to_json()}
            self.write(response)
        except OrganizationPermission.DoesNotExist, error:
            raise HTTPError(404, **{'reason': self.error_message(error)})

