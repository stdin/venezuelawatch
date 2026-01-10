#!/usr/bin/env python3
"""
Set up BigQuery ETL pipeline from PostgreSQL to BigQuery.

Creates:
1. BigQuery Connection to Cloud SQL PostgreSQL
2. Scheduled Query to run ETL daily at 2 AM UTC

Prerequisites:
- BigQuery Connection API enabled: gcloud services enable bigqueryconnection.googleapis.com
- Secret Manager secrets: POSTGRES_USER, POSTGRES_PASSWORD
- Cloud SQL instance connection name in env: CLOUD_SQL_INSTANCE

Usage:
    python backend/forecasting/setup_etl.py --project venezuelawatch
"""

import argparse
import sys
import os
from pathlib import Path
from google.cloud import bigquery
from google.cloud import bigquery_connection_v1
from google.cloud import bigquery_datatransfer_v1
from google.cloud import secretmanager
from google.protobuf.timestamp_pb2 import Timestamp
from datetime import datetime, timezone


def get_secret(project_id: str, secret_id: str) -> str:
    """Retrieve secret from Secret Manager.

    Args:
        project_id: GCP project ID
        secret_id: Secret name

    Returns:
        Secret value as string
    """
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        print(f"⚠️  Warning: Could not access secret {secret_id}: {e}", file=sys.stderr)
        return None


def create_cloudsql_connection(
    project_id: str,
    location: str,
    connection_id: str,
    instance_name: str,
    database: str,
    username: str,
    password: str
) -> str:
    """Create BigQuery Connection to Cloud SQL PostgreSQL.

    Args:
        project_id: GCP project ID
        location: GCP region (e.g., 'us-central1')
        connection_id: Connection ID (e.g., 'postgresql-conn')
        instance_name: Cloud SQL instance connection name
        database: Database name
        username: PostgreSQL username
        password: PostgreSQL password

    Returns:
        Full connection resource name
    """
    client = bigquery_connection_v1.ConnectionServiceClient()
    parent = f"projects/{project_id}/locations/{location}"
    connection_name = f"{parent}/connections/{connection_id}"

    # Check if connection already exists
    try:
        existing = client.get_connection(name=connection_name)
        print(f"✓ Connection {connection_name} already exists")
        return connection_name
    except Exception:
        # Connection doesn't exist, create it
        pass

    # Create CloudSqlProperties
    cloud_sql = bigquery_connection_v1.CloudSqlProperties(
        instance_id=instance_name,
        database=database,
        type_=bigquery_connection_v1.CloudSqlProperties.DatabaseType.POSTGRES,
        credential=bigquery_connection_v1.CloudSqlCredential(
            username=username,
            password=password
        )
    )

    connection = bigquery_connection_v1.Connection(
        cloud_sql=cloud_sql,
        description="Connection to Cloud SQL PostgreSQL for BigQuery Federated Query ETL"
    )

    request = bigquery_connection_v1.CreateConnectionRequest(
        parent=parent,
        connection_id=connection_id,
        connection=connection
    )

    try:
        created = client.create_connection(request=request)
        print(f"✓ Created connection {connection_name}")
        return connection_name
    except Exception as e:
        print(f"❌ Error creating connection: {e}", file=sys.stderr)
        if "bigqueryconnection.googleapis.com" in str(e):
            print("\n💡 Enable BigQuery Connection API:", file=sys.stderr)
            print("   gcloud services enable bigqueryconnection.googleapis.com", file=sys.stderr)
        raise


def create_scheduled_query(
    project_id: str,
    location: str,
    connection_name: str,
    query_sql: str
) -> str:
    """Create scheduled query to run ETL daily.

    Args:
        project_id: GCP project ID
        location: GCP region
        connection_name: Full connection resource name
        query_sql: SQL query to run

    Returns:
        Transfer config name
    """
    client = bigquery_datatransfer_v1.DataTransferServiceClient()
    parent = f"projects/{project_id}/locations/{location}"

    # Replace placeholders in SQL
    connection_id = connection_name.split('/')[-1]
    query_sql = query_sql.replace('PROJECT_ID', project_id)
    query_sql = query_sql.replace('CONNECTION_ID', connection_id)

    # Create transfer config
    transfer_config = bigquery_datatransfer_v1.TransferConfig(
        display_name="PostgreSQL to BigQuery ETL for Vertex AI Forecasting",
        data_source_id="scheduled_query",
        destination_dataset_id="intelligence",
        schedule="every day 02:00",  # Daily at 2 AM UTC
        params={
            "query": query_sql,
            "destination_table_name_template": "entity_risk_training_data",
            "write_disposition": "WRITE_TRUNCATE",  # Replace table on each run
            "partitioning_field": ""
        }
    )

    try:
        # Check if scheduled query already exists
        configs = client.list_transfer_configs(parent=parent)
        for config in configs:
            if config.display_name == transfer_config.display_name:
                print(f"✓ Scheduled query already exists: {config.name}")
                return config.name

        # Create new scheduled query
        created = client.create_transfer_config(
            parent=parent,
            transfer_config=transfer_config
        )
        print(f"✓ Created scheduled query: {created.name}")
        print(f"  Schedule: every day 02:00 UTC")
        print(f"  Query: {len(query_sql)} characters")
        return created.name

    except Exception as e:
        print(f"❌ Error creating scheduled query: {e}", file=sys.stderr)
        raise


def main():
    """Main entry point for ETL setup."""
    parser = argparse.ArgumentParser(
        description="Set up BigQuery ETL pipeline from PostgreSQL to BigQuery"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GCP project ID (e.g., venezuelawatch)"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP region (default: us-central1)"
    )
    parser.add_argument(
        "--connection-id",
        default="postgresql-conn",
        help="Connection ID (default: postgresql-conn)"
    )
    parser.add_argument(
        "--database",
        default="venezuelawatch",
        help="PostgreSQL database name (default: venezuelawatch)"
    )

    args = parser.parse_args()

    # Get Cloud SQL instance from environment
    instance_name = os.getenv('CLOUD_SQL_INSTANCE')
    if not instance_name:
        print("❌ Error: CLOUD_SQL_INSTANCE environment variable not set", file=sys.stderr)
        print("   Set it to your Cloud SQL connection name (e.g., project:region:instance)", file=sys.stderr)
        sys.exit(1)

    print(f"Using Cloud SQL instance: {instance_name}")

    # Get database credentials from Secret Manager
    username = get_secret(args.project, 'POSTGRES_USER')
    password = get_secret(args.project, 'POSTGRES_PASSWORD')

    if not username or not password:
        print("❌ Error: Could not retrieve database credentials from Secret Manager", file=sys.stderr)
        print("   Required secrets: POSTGRES_USER, POSTGRES_PASSWORD", file=sys.stderr)
        sys.exit(1)

    print(f"Retrieved credentials for user: {username}")

    try:
        # Create BigQuery connection
        connection_name = create_cloudsql_connection(
            project_id=args.project,
            location=args.location,
            connection_id=args.connection_id,
            instance_name=instance_name,
            database=args.database,
            username=username,
            password=password
        )

        # Load ETL query SQL
        sql_path = Path(__file__).parent / 'etl_query.sql'
        with open(sql_path) as f:
            query_sql = f.read()

        # Create scheduled query
        transfer_config_name = create_scheduled_query(
            project_id=args.project,
            location=args.location,
            connection_name=connection_name,
            query_sql=query_sql
        )

        print("\n✅ ETL setup complete!")
        print(f"\nVerify scheduled query:")
        print(f"  bq ls --transfer_config --project={args.project}")
        print(f"\nManually trigger for testing:")
        print(f"  bq mk --transfer_run --run_time='{datetime.now(timezone.utc).isoformat()}' {transfer_config_name}")
        print(f"\nCheck results:")
        print(f"  bq query --project={args.project} 'SELECT COUNT(*) FROM intelligence.entity_risk_training_data'")

    except Exception as e:
        print(f"\n❌ Setup failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
