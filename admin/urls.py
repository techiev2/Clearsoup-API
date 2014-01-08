# coding=utf-8
"""
Clearsoup SuperAdmin app urls module
Contains url maps for the SuperAdmin app controllers
"""
from admin.handlers import AdminHandler

URLS = [('/api/_su_/?$', AdminHandler)
        ]

__all__ = ['URLS']
