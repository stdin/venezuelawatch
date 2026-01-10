from google.cloud import aiplatform
import argparse


def train_entity_risk_model(project_id: str, location: str = 'us-central1'):
    """Train Vertex AI forecasting model on BigQuery data."""

    aiplatform.init(project=project_id, location=location)

    # Create dataset from BigQuery table
    dataset = aiplatform.TimeSeriesDataset.create(
        display_name='entity-risk-forecasting',
        bq_source=f'bq://{project_id}.intelligence.entity_risk_training_data',
        time_column='mentioned_at',
        time_series_identifier_column='entity_id',
        target_column='risk_score'
    )

    # Define training job with AutoML
    training_job = aiplatform.AutoMLForecastingTrainingJob(
        display_name='entity-risk-tide-model',
        optimization_objective='minimize-rmse',
        column_specs={
            'sanctions_risk': 'numeric',
            'political_risk': 'numeric',
            'economic_risk': 'numeric',
            'supply_chain_risk': 'numeric'
        }
    )

    # Train model (1-4 hours)
    model = training_job.run(
        dataset=dataset,
        target_column='risk_score',
        time_column='mentioned_at',
        time_series_identifier_column='entity_id',
        forecast_horizon=30,  # 30 days
        data_granularity_unit='day',
        data_granularity_count=1,
        training_fraction_split=0.8,
        validation_fraction_split=0.1,
        test_fraction_split=0.1,
        budget_milli_node_hours=1000,  # Auto-scales training time
    )

    print(f"Model trained: {model.resource_name}")
    print(f"Model display name: {model.display_name}")

    return model


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, help='GCP project ID')
    parser.add_argument('--location', default='us-central1', help='GCP region')
    args = parser.parse_args()

    train_entity_risk_model(args.project, args.location)
