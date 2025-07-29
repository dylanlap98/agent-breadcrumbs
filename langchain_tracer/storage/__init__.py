"""
Storage backends for trace events
"""

from .csv_storage import CSVStorage
from .json_storage import JSONStorage

__all__ = [
    "CSVStorage",
    "JSONStorage",
]
