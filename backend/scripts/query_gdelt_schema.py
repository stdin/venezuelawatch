#!/usr/bin/env python
"""
Query GDELT BigQuery dataset to inspect available tables and schemas.
"""
import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'venezuelawatch.settings')
django.setup()

from google.cloud import bigquery
from django.conf import settings


def list_gdelt_tables():
    """List all tables in gdelt-bq.gdeltv2 dataset."""
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)

    print("=" * 80)
    print("GDELT BigQuery Dataset: gdelt-bq.gdeltv2")
    print("=" * 80)
    print()

    try:
        # List tables in gdeltv2 dataset
        tables = client.list_tables("gdelt-bq.gdeltv2")

        print("Available Tables:")
        print("-" * 80)
        table_list = []
        for table in tables:
            table_list.append(table.table_id)
            print(f"  - {table.table_id}")

        print()
        print(f"Total tables: {len(table_list)}")
        print()

        return table_list

    except Exception as e:
        print(f"Error listing tables: {e}")
        return []


def get_table_schema(table_id: str):
    """Get schema for a specific table."""
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)

    print("=" * 80)
    print(f"Schema for: gdelt-bq.gdeltv2.{table_id}")
    print("=" * 80)
    print()

    try:
        table_ref = client.get_table(f"gdelt-bq.gdeltv2.{table_id}")

        print(f"Table type: {table_ref.table_type}")
        print(f"Created: {table_ref.created}")
        print(f"Rows: {table_ref.num_rows:,}" if table_ref.num_rows else "Rows: N/A")
        print(f"Size: {table_ref.num_bytes / 1024 / 1024 / 1024:.2f} GB" if table_ref.num_bytes else "Size: N/A")
        print()

        # Check if partitioned
        if table_ref.time_partitioning:
            print(f"Time Partitioning: {table_ref.time_partitioning.type_}")
            print(f"Partition Field: {table_ref.time_partitioning.field or '_PARTITIONTIME'}")
            print()

        print("Schema Fields:")
        print("-" * 80)
        print(f"{'Field Name':<40} {'Type':<20} {'Mode':<10}")
        print("-" * 80)

        for field in table_ref.schema:
            print(f"{field.name:<40} {field.field_type:<20} {field.mode:<10}")

        print()
        print(f"Total fields: {len(table_ref.schema)}")
        print()

        return table_ref.schema

    except Exception as e:
        print(f"Error getting schema: {e}")
        return None


def sample_data(table_id: str, limit: int = 5):
    """Get sample data from table."""
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)

    print("=" * 80)
    print(f"Sample Data from: gdelt-bq.gdeltv2.{table_id}")
    print("=" * 80)
    print()

    try:
        # Query with partition filter if it's a partitioned table
        if "_partitioned" in table_id:
            query = f"""
                SELECT *
                FROM `gdelt-bq.gdeltv2.{table_id}`
                WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
                LIMIT {limit}
            """
        else:
            query = f"""
                SELECT *
                FROM `gdelt-bq.gdeltv2.{table_id}`
                LIMIT {limit}
            """

        print(f"Query: {query}")
        print()

        results = client.query(query).result()

        rows = list(results)
        if rows:
            print(f"Found {len(rows)} sample rows:")
            print("-" * 80)
            for i, row in enumerate(rows, 1):
                print(f"\nRow {i}:")
                for key, value in dict(row).items():
                    # Truncate long values
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"  {key}: {value_str}")
        else:
            print("No data found")

        print()

    except Exception as e:
        print(f"Error querying sample data: {e}")


def query_venezuela_events():
    """Query recent Venezuela events to test filter."""
    client = bigquery.Client(project=settings.GCP_PROJECT_ID)

    print("=" * 80)
    print("Venezuela Events Query Test")
    print("=" * 80)
    print()

    try:
        query = """
            SELECT
                GLOBALEVENTID,
                SQLDATE,
                Actor1Name,
                Actor2Name,
                EventCode,
                QuadClass,
                GoldsteinScale,
                NumMentions,
                AvgTone,
                ActionGeo_FullName,
                ActionGeo_CountryCode,
                SOURCEURL
            FROM `gdelt-bq.gdeltv2.events_partitioned`
            WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)
            AND (
                ActionGeo_CountryCode = 'VE'
                OR Actor1CountryCode = 'VE'
                OR Actor2CountryCode = 'VE'
            )
            ORDER BY SQLDATE DESC
            LIMIT 10
        """

        print("Query:")
        print(query)
        print()

        results = client.query(query).result()

        rows = list(results)
        print(f"Found {len(rows)} Venezuela events in last 2 days:")
        print("-" * 80)

        for i, row in enumerate(rows, 1):
            print(f"\nEvent {i}:")
            print(f"  ID: {row.GLOBALEVENTID}")
            print(f"  Date: {row.SQLDATE}")
            print(f"  Actor1: {row.Actor1Name}")
            print(f"  Actor2: {row.Actor2Name}")
            print(f"  Event Code: {row.EventCode}")
            print(f"  Quad Class: {row.QuadClass}")
            print(f"  Goldstein Scale: {row.GoldsteinScale}")
            print(f"  Mentions: {row.NumMentions}")
            print(f"  Tone: {row.AvgTone}")
            print(f"  Location: {row.ActionGeo_FullName} ({row.ActionGeo_CountryCode})")
            print(f"  URL: {row.SOURCEURL[:100] if row.SOURCEURL else 'N/A'}")

        print()

    except Exception as e:
        print(f"Error querying Venezuela events: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("GDELT BigQuery Dataset Inspector")
    print()

    # List all tables
    tables = list_gdelt_tables()

    # Get schema for key tables
    if "events_partitioned" in tables:
        get_table_schema("events_partitioned")

    if "eventmentions_partitioned" in tables:
        get_table_schema("eventmentions_partitioned")

    if "gkg_partitioned" in tables:
        get_table_schema("gkg_partitioned")

    # Test Venezuela query
    if "events_partitioned" in tables:
        query_venezuela_events()
