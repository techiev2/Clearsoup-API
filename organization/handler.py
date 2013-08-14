'''
Created on 13-Aug-2013

@author: someshs
'''
import sys
from datetime import datetime
from tornado.web import HTTPError
from requires.base import BaseHandler, authenticated
from datamodels.organization import Organization, OrganizationProfile
from mongoengine.errors import ValidationError
from utils.dumpers import json_dumper

sys.dont_write_bytecode = True

class OrganizationHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'PUT': ('name',),
        }
    data = {}

    def __init__(self, *args, **kwargs):
        super(OrganizationHandler, self).__init__(*args, **kwargs)

    def clean_request(self):
        self.data.update({'created_by': self.current_user,
                         'updated_by': self.current_user,
                         'admin': self.current_user})


    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            return Organization.get_organization_object(organization)

    @authenticated
    def get(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            self.write(org.to_json())

    @authenticated
    def post(self, *args, **kwargs):
        pass
#        organization  = kwargs.get('organization', None)
#        response = {}
#        org = self.validate_request(organization)
#        if not org:
#            self.send_error(404)
#        else:
#            OrganizationProfile(**self.data)

    @authenticated
    def put(self, *args, **kwargs):
        OrganizationProfile.objects.delete()
        self.clean_request()
        org = Organization(**self.data)
        try:
            org.save(validate=True, clean=True)
            self.write(org.to_json())
            OrganizationProfile.objects.create(organization=org,
                                               created_by=self.current_user,
                                               updated_by=self.current_user)
        except ValidationError, error:
            raise HTTPError(403, **{'reason':self.error_message(error)})

    @authenticated
    def delete(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            org.delete()
            self.write({'message': 'Deleted Successfully.'})


class OrgProfileHandler(BaseHandler):
    SUPPORTED_METHODS = ('GET', 'POST', 'PUT', 'DELETE')
    REQUIRED_FIELDS   = {
        'PUT': ('display_name', 'url', 'location'),
        'DELETE' : ('id',),
        }
    data = {}

    def __init__(self, *args, **kwargs):
        super(OrgProfileHandler, self).__init__(*args, **kwargs)

    def clean_request(self, org):
        self.data.update({'created_by': self.current_user,
                         'updated_by': self.current_user,
                         'organization': org})


    def validate_request(self, organization):
        if not organization:
            self.send_error(400)
        else:
            return Organization.get_organization_object(organization)

    @authenticated
    def get(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        response = {}
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            response['organization'] = org.to_json()
            response['organization_profile'] = json_dumper(
                                               org.get_organization_profile())
            self.write(response)

    @authenticated
    def post(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            org_profile = org.get_organization_profile()
            temp_data = {'set__'+field: self.data[field] for field 
                         in OrganizationProfile._fields.keys() 
                         if field in self.data.keys()}
            temp_data.update({'set__updated_by': self.current_user,
                              'set__updated_at': datetime.utcnow()})
            org_profile.update(**temp_data)
            self.write(org_profile.to_json())

    @authenticated
    def put(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            self.clean_request(org)
            org_profile = OrganizationProfile(**self.data)
            try:
                org_profile.save()
                self.write(org_profile.to_json())
            except ValidationError, error:
                raise HTTPError(403, **{'reason':self.error_message(error)})

    @authenticated
    def delete(self, *args, **kwargs):
        organization  = kwargs.get('organization', None)
        org = self.validate_request(organization)
        if not org:
            self.send_error(404)
        else:
            org.get_organization_profile().delete()
            self.write({'message': 'Deleted Successfully.'})
