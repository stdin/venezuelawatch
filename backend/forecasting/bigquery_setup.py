#!/usr/bin/env python3
"""
BigQuery dataset and table setup for Vertex AI forecasting.

Creates:
- Dataset: intelligence (location: us-central1)
- Table: entity_risk_training_data with schema for Vertex AI

Usage:
    python backend/forecasting/bigquery_setup.py --project venezuelawatch
"""

import argparse
import sys
from google.cloud import bigquery
from google.api_core.exceptions import Conflict


def create_dataset(client: bigquery.Client, dataset_id: str, location: str = "us-central1") -> None:
    """Create BigQuery dataset if it doesn't exist.

    Args:
        client: BigQuery client instance
        dataset_id: Dataset ID (e.g., 'intelligence')
        location: GCP region for dataset
    """
    dataset_ref = f"{client.project}.{dataset_id}"

    try:
        client.get_dataset(dataset_ref)
        print(f"✓ Dataset {dataset_ref} already exists")
    except Exception:
        # Dataset doesn't exist, create it
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        dataset = client.create_dataset(dataset, timeout=30)
        print(f"✓ Created dataset {dataset_ref} in {location}")


def create_table(client: bigquery.Client, dataset_id: str, table_id: str) -> None:
    """Create entity_risk_training_data table with Vertex AI compatible schema.

    Schema designed for narrow (long) format time-series forecasting:
    - entity_id: Time series identifier
    - mentioned_at: Time column (daily granularity)
    - risk_score: Target variable for forecasting
    - Dimensional breakdowns: sanctions, political, economic, supply_chain risk

    Args:
        client: BigQuery client instance
        dataset_id: Dataset ID
        table_id: Table ID (e.g., 'entity_risk_training_data')
    """
    table_ref = f"{client.project}.{dataset_id}.{table_id}"

    try:
        client.get_table(table_ref)
        print(f"✓ Table {table_ref} already exists")
        return
    except Exception:
        # Table doesn't exist, create it
        pass

    # Define schema for Vertex AI forecasting
    schema = [
        bigquery.SchemaField("entity_id", "STRING", mode="REQUIRED",
                           description="Entity identifier (time series ID)"),
        bigquery.SchemaField("mentioned_at", "TIMESTAMP", mode="REQUIRED",
                           description="Event timestamp aggregated to daily granularity"),
        bigquery.SchemaField("risk_score", "FLOAT64", mode="REQUIRED",
                           description="Overall risk score (target for forecasting)"),
        bigquery.SchemaField("sanctions_risk", "FLOAT64", mode="NULLABLE",
                           description="Sanctions-related risk dimension"),
        bigquery.SchemaField("political_risk", "FLOAT64", mode="NULLABLE",
                           description="Political disruption risk dimension"),
        bigquery.SchemaField("economic_risk", "FLOAT64", mode="NULLABLE",
                           description="Economic volatility risk dimension"),
        bigquery.SchemaField("supply_chain_risk", "FLOAT64", mode="NULLABLE",
                           description="Supply chain disruption risk dimension"),
    ]

    table = bigquery.Table(table_ref, schema=schema)
    table.description = "Entity risk scores aggregated daily for Vertex AI forecasting training"

    # Add time partitioning on mentioned_at for query performance
    table.time_partitioning = bigquery.TimePartitioning(
        type_=bigquery.TimePartitioningType.DAY,
        field="mentioned_at"
    )

    table = client.create_table(table)
    print(f"✓ Created table {table_ref}")
    print(f"  - Schema: {len(schema)} columns")
    print(f"  - Partitioning: DAY on mentioned_at")
    print(f"  - Description: {table.description}")


def main():
    """Main entry point for BigQuery setup."""
    parser = argparse.ArgumentParser(
        description="Create BigQuery dataset and table for Vertex AI forecasting"
    )
    parser.add_argument(
        "--project",
        required=True,
        help="GCP project ID (e.g., venezuelawatch)"
    )
    parser.add_argument(
        "--dataset",
        default="intelligence",
        help="BigQuery dataset ID (default: intelligence)"
    )
    parser.add_argument(
        "--table",
        default="entity_risk_training_data",
        help="BigQuery table ID (default: entity_risk_training_data)"
    )
    parser.add_argument(
        "--location",
        default="us-central1",
        help="GCP region (default: us-central1)"
    )

    args = parser.parse_args()

    try:
        # Initialize BigQuery client with default credentials (ADC)
        client = bigquery.Client(project=args.project)
        print(f"Using project: {args.project}")

        # Create dataset
        create_dataset(client, args.dataset, args.location)

        # Create table
        create_table(client, args.dataset, args.table)

        print("\n✅ BigQuery setup complete!")
        print(f"\nVerify with:")
        print(f"  gcloud config set project {args.project}")
        print(f"  bq show {args.dataset}.{args.table}")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
