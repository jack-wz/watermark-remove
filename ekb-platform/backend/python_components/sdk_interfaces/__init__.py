# EKB Platform Python SDK Interfaces
# This package defines the abstract base classes (interfaces)
# that Python plugins should implement to be compatible with the EKB platform.

from .connectors import SourceConnector
from .functions import EnrichmentFunction

__all__ = [
    "SourceConnector",
    "EnrichmentFunction",
]
