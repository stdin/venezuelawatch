from google.cloud import aiplatform
import argparse


def deploy_forecasting_endpoint(
    project_id: str,
    model_name: str,
    location: str = 'us-central1'
):
    """Deploy trained model to endpoint for predictions."""

    aiplatform.init(project=project_id, location=location)

    # Get trained model
    model = aiplatform.Model(model_name)

    # Deploy to endpoint with autoscaling
    endpoint = model.deploy(
        machine_type='n1-standard-4',
        min_replica_count=1,
        max_replica_count=10,
        accelerator_type=None,  # No GPU needed for TiDE inference
        traffic_percentage=100,
        deploy_request_timeout=1800,  # 30 min timeout for deployment
    )

    print(f"Endpoint deployed: {endpoint.resource_name}")
    print(f"Endpoint display name: {endpoint.display_name}")
    print(f"\nAdd to settings:")
    print(f"VERTEX_AI_ENDPOINT_ID = '{endpoint.resource_name}'")

    return endpoint


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True)
    parser.add_argument('--model', required=True, help='Model resource name from training')
    parser.add_argument('--location', default='us-central1')
    args = parser.parse_args()

    deploy_forecasting_endpoint(args.project, args.model, args.location)
