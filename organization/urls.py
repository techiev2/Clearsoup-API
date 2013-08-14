'''
Created on 13-Aug-2013

@author: someshs
'''

from organization.handler import OrganizationHandler

URLS = [('/api/projects/?$', OrganizationHandler),
       ]

__all__ = ['URLS']

