"""
Prismic.io python library.
"""

__title__ = 'prismic-httpx'
__version__ = '0.0.2'
__author__ = 'Rémi DEBETTE'
__license__ = 'Apache 2'

from .api import get, Api, SearchForm, Document
from .fragments import Fragment

# Set a default logger to prevent "No handler found" warnings
import logging
try:  # Python >=2.7
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())

EXPERIMENTS_COOKIE = "io.prismic.experiment"
PREVIEW_COOKIE = "io.prismic.preview"
