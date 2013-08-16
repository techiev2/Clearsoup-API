'''
Created on 13-Aug-2013

@author: someshs
'''

from organization.handler import OrganizationHandler, OrgProfileHandler

URLS = [('/api/organization/?$', OrganizationHandler),
        ('/api/organization/(?P<organization>.*?)/settings/?$', OrgProfileHandler),
        ('/api/organization/(?P<organization>.*?)/?$', OrganizationHandler),
       ]

__all__ = ['URLS']

