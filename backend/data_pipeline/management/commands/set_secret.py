"""
Management command to set secrets in GCP Secret Manager.

Usage:
    python manage.py set_secret <secret_id> <value>

Example:
    python manage.py set_secret api-fred-key "your-api-key-here"
"""
from django.core.management.base import BaseCommand, CommandError
from data_pipeline.services.secrets import SecretManagerClient


class Command(BaseCommand):
    help = 'Set a secret in GCP Secret Manager'

    def add_arguments(self, parser):
        parser.add_argument(
            'secret_id',
            type=str,
            help='Secret identifier (e.g., api-fred-key)'
        )
        parser.add_argument(
            'value',
            type=str,
            help='Secret value to store'
        )

    def handle(self, *args, **options):
        secret_id = options['secret_id']
        value = options['value']

        try:
            client = SecretManagerClient()
            client.set_secret(secret_id, value)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully set secret '{secret_id}' in Secret Manager"
                )
            )

        except RuntimeError as e:
            # Secret Manager not enabled - provide helpful error
            self.stdout.write(
                self.style.WARNING(str(e))
            )
            self.stdout.write(
                self.style.NOTICE(
                    f"\nFor local development, set environment variable instead:\n"
                    f"export {secret_id.upper().replace('-', '_')}='{value}'"
                )
            )
            raise CommandError("Secret Manager not enabled")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to set secret: {e}")
            )
            raise CommandError(f"Failed to set secret: {e}")
