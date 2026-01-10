"""
Convention-based adapter registry for automatic discovery.

This module implements the plugin discovery system. Just drop a file in this directory
following naming conventions and it will be auto-discovered.

**Convention:**
- File naming: `{source}_adapter.py` (e.g., gdelt_adapter.py, reliefweb_adapter.py)
- Class naming: `{Source}Adapter` (e.g., GdeltAdapter, RelicfwebAdapter)
- Must inherit from DataSourceAdapter
- Must define source_name, schedule_frequency, default_lookback_minutes

**Example:**

File: data_pipeline/adapters/gdelt_adapter.py

    from data_pipeline.adapters.base import DataSourceAdapter
    from api.bigquery_models import Event

    class GdeltAdapter(DataSourceAdapter):
        source_name = "gdelt"
        schedule_frequency = "*/15 * * * *"
        default_lookback_minutes = 20

        def fetch(self, start_time, end_time, limit=100):
            # ... implementation ...

        def transform(self, raw_events):
            # ... implementation ...

        def validate(self, event):
            # ... implementation ...

That's it! The registry will find it automatically on next import.

**Usage:**

    from data_pipeline.adapters.registry import adapter_registry

    # List all discovered adapters
    adapters = adapter_registry.list_adapters()
    # ['gdelt', 'reliefweb', 'fred']

    # Get adapter class
    GdeltAdapter = adapter_registry.get_adapter('gdelt')
    adapter_instance = GdeltAdapter()

    # Get metadata
    meta = adapter_registry.get_metadata('gdelt')
    # {'source_name': 'gdelt', 'schedule_frequency': '*/15 * * * *', ...}

    # Track runs (for observability)
    adapter_registry.record_run('gdelt', success=True, events_count=150, duration_ms=2340)
    health = adapter_registry.get_health('gdelt')
    # {'last_run': datetime(...), 'last_success': True, 'total_runs': 42, 'success_rate': 0.95}
"""

import os
import importlib
import inspect
import logging
from datetime import datetime
from typing import Dict, Type, Optional, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """
    Singleton registry that auto-discovers data source adapters.

    Discovery happens on instantiation by scanning adapters/ directory for
    files matching {source}_adapter.py pattern.
    """

    def __init__(self):
        """Initialize registry and discover adapters."""
        self._adapters: Dict[str, Type['DataSourceAdapter']] = {}
        self._health: Dict[str, Dict[str, Any]] = {}
        self.discover_adapters()

    def discover_adapters(self) -> Dict[str, Type['DataSourceAdapter']]:
        """
        Scan adapters/ directory for adapter modules and auto-register them.

        Convention:
        - File: {source}_adapter.py
        - Class: {Source}Adapter (title case, e.g., GdeltAdapter)
        - Must inherit from DataSourceAdapter

        Returns:
            Dict mapping source_name to adapter class

        Note:
            - Skips base.py and registry.py
            - Gracefully handles missing/invalid files (logs warning, continues)
            - Invalid adapters logged but don't crash discovery
        """
        from data_pipeline.adapters.base import DataSourceAdapter

        # Get directory containing this file
        adapters_dir = Path(__file__).parent

        # Scan for *_adapter.py files
        adapter_files = adapters_dir.glob('*_adapter.py')

        discovered_count = 0

        for file_path in adapter_files:
            module_name = file_path.stem  # e.g., 'gdelt_adapter'

            # Skip non-adapter files
            if module_name in ('base', 'registry', '__init__'):
                continue

            try:
                # Import module dynamically
                full_module_name = f'data_pipeline.adapters.{module_name}'
                module = importlib.import_module(full_module_name)

                # Extract source name from filename: gdelt_adapter → gdelt
                source_name = module_name.replace('_adapter', '')

                # Expected class name: gdelt → GdeltAdapter
                expected_class_name = f"{source_name.title()}Adapter"

                # Find class in module
                adapter_class = None
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's the expected class and inherits from DataSourceAdapter
                    if (name == expected_class_name and
                        issubclass(obj, DataSourceAdapter) and
                        obj is not DataSourceAdapter):
                        adapter_class = obj
                        break

                if adapter_class is None:
                    logger.warning(
                        f"No valid adapter class found in {module_name}.py. "
                        f"Expected class name: {expected_class_name} inheriting from DataSourceAdapter"
                    )
                    continue

                # Register by source_name attribute
                registry_key = adapter_class.source_name
                self._adapters[registry_key] = adapter_class
                discovered_count += 1

                logger.info(
                    f"Discovered adapter: {registry_key}",
                    extra={
                        'source': registry_key,
                        'class': expected_class_name,
                        'module': full_module_name,
                        'schedule': adapter_class.schedule_frequency
                    }
                )

            except Exception as e:
                logger.warning(
                    f"Failed to load adapter from {module_name}.py: {e}",
                    exc_info=True
                )
                continue

        logger.info(
            f"Adapter discovery complete: {discovered_count} adapters registered",
            extra={'adapters': list(self._adapters.keys())}
        )

        return self._adapters

    def get_adapter(self, source_name: str) -> Optional[Type['DataSourceAdapter']]:
        """
        Retrieve adapter class by source name.

        Args:
            source_name: Source identifier (e.g., 'gdelt', 'reliefweb')

        Returns:
            Adapter class if found, None otherwise

        Example:
            GdeltAdapter = registry.get_adapter('gdelt')
            if GdeltAdapter:
                adapter = GdeltAdapter()
                events = adapter.fetch(...)
        """
        return self._adapters.get(source_name)

    def list_adapters(self) -> List[str]:
        """
        Get list of all registered adapter names.

        Returns:
            List of source_name strings

        Example:
            adapters = registry.list_adapters()
            # ['gdelt', 'reliefweb', 'fred', 'worldbank']
        """
        return list(self._adapters.keys())

    def get_metadata(self, source_name: str) -> Dict[str, Any]:
        """
        Get adapter metadata (class attributes).

        Args:
            source_name: Source identifier

        Returns:
            Dict with source_name, schedule_frequency, default_lookback_minutes
            Empty dict if adapter not found

        Example:
            meta = registry.get_metadata('gdelt')
            # {
            #     'source_name': 'gdelt',
            #     'schedule_frequency': '*/15 * * * *',
            #     'default_lookback_minutes': 20
            # }
        """
        adapter_class = self.get_adapter(source_name)
        if not adapter_class:
            return {}

        return {
            'source_name': adapter_class.source_name,
            'schedule_frequency': adapter_class.schedule_frequency,
            'default_lookback_minutes': adapter_class.default_lookback_minutes
        }

    def record_run(
        self,
        source_name: str,
        success: bool,
        events_count: int,
        duration_ms: int
    ) -> None:
        """
        Record adapter run for health tracking.

        Args:
            source_name: Source identifier
            success: Whether run completed successfully
            events_count: Number of events processed
            duration_ms: Execution duration in milliseconds

        Note:
            Health metrics stored in-memory (not persistent).
            Used for observability and debugging.

        Example:
            registry.record_run(
                source_name='gdelt',
                success=True,
                events_count=150,
                duration_ms=2340
            )
        """
        if source_name not in self._health:
            self._health[source_name] = {
                'total_runs': 0,
                'successful_runs': 0,
                'last_run': None,
                'last_success': None,
                'last_events_count': None,
                'last_duration_ms': None
            }

        health = self._health[source_name]
        health['total_runs'] += 1
        if success:
            health['successful_runs'] += 1
        health['last_run'] = datetime.utcnow()
        health['last_success'] = success
        health['last_events_count'] = events_count
        health['last_duration_ms'] = duration_ms

    def get_health(self, source_name: str) -> Dict[str, Any]:
        """
        Get health metrics for an adapter.

        Args:
            source_name: Source identifier

        Returns:
            Dict with health metrics:
            - last_run: datetime of last execution
            - last_success: bool, whether last run succeeded
            - total_runs: int, total executions
            - success_rate: float (0.0-1.0)
            - last_events_count: int, events from last run
            - last_duration_ms: int, duration of last run

        Example:
            health = registry.get_health('gdelt')
            if health['success_rate'] < 0.8:
                logger.warning(f"Low success rate for {source_name}")
        """
        if source_name not in self._health:
            return {
                'last_run': None,
                'last_success': None,
                'total_runs': 0,
                'success_rate': 0.0,
                'last_events_count': None,
                'last_duration_ms': None
            }

        health = self._health[source_name]
        success_rate = (
            health['successful_runs'] / health['total_runs']
            if health['total_runs'] > 0
            else 0.0
        )

        return {
            'last_run': health['last_run'],
            'last_success': health['last_success'],
            'total_runs': health['total_runs'],
            'success_rate': success_rate,
            'last_events_count': health['last_events_count'],
            'last_duration_ms': health['last_duration_ms']
        }


# Module-level singleton - auto-discovers on import
adapter_registry = AdapterRegistry()
