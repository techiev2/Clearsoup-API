'''
Created on 13-Aug-2013

@author: someshs
'''

from organization.handler import OrganizationHandler, OrgProfileHandler
from organization.project import OrgProjectHandler
from organization.permission import OrgPermissionHandler,\
 ProjectPermissionHandler
from organization.team import TeamHandler
from organization.members import OrgMemeberHandler


URLS = [('/api/organization/?$', OrganizationHandler),
        ('/api/(?P<organization>.*?)/project/?$', OrgProjectHandler),
        ('/api/(?P<organization>.*?)/project/permission/?$',
                                                ProjectPermissionHandler),
        ('/api/(?P<organization>.*?)/permission/?$', OrgPermissionHandler),
        ('/api/(?P<organization>.*?)/team/?$', TeamHandler),
        ('/api/(?P<organization>.*?)/member/?$', OrgMemeberHandler),
        ('/api/(?P<organization>.*?)/settings/?$', OrgProfileHandler),
        ('/api/(?P<organization>.*?)/?$', OrganizationHandler),
       ]

__all__ = ['URLS']

