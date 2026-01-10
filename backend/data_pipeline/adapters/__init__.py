"""
Data source adapter plugin system.

Import DataSourceAdapter to create new adapters.
Import adapter_registry to discover and access registered adapters.
"""

from data_pipeline.adapters.base import DataSourceAdapter

__all__ = ['DataSourceAdapter']
