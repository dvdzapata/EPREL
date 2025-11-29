"""
EPREL Database Sync Package

This package provides tools for synchronizing product data from the 
European Product Registry for Energy Labelling (EPREL) to a PostgreSQL database.
"""

from .eprel_client import EPRELClient, EPRELAPIError
from .database import Database, DatabaseError
from .sync_service import SyncService

__version__ = "1.0.0"
__all__ = [
    'EPRELClient',
    'EPRELAPIError',
    'Database',
    'DatabaseError',
    'SyncService',
]
