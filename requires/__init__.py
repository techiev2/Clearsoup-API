
"""
Requires for app
"""
import sys
sys.dont_write_bytecode = True
import requires.settings
from requires.settings import SERVER, LOOP, PORT, SETTINGS

__all__ = ['SERVER', 'LOOP', 'PORT', 'SETTINGS']
