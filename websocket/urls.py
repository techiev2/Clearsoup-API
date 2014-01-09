# coding=utf-8
"""Websocket app urls module. Provides url maps for Websocket handlers"""
from .handlers import AppWebSocketHandler

URLS = [('/_socket', AppWebSocketHandler)]

__all__ = ['URLS']

if __name__ == '__main__':
    pass
