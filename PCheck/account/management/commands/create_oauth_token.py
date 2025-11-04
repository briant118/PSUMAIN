from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from account.models import OAuthToken


class Command(BaseCommand):
    help = 'Create sample OAuth tokens for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the token',
            default='test@psu.palawan.edu.ph'
        )
        parser.add_argument(
            '--token',
            type=str,
            help='Token key (if not provided, will generate a sample)',
            default='PSU_TOKEN_12345'
        )

    def handle(self, *args, **options):
        email = options['email']
        token_key = options['token']
        
        # Create OAuth token
        oauth_token, created = OAuthToken.objects.get_or_create(
            token_key=token_key,
            defaults={
                'user_email': email,
                'is_active': True,
                'expires_at': timezone.now() + timedelta(days=30)  # Expires in 30 days
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created OAuth token:\n'
                    f'Token: {token_key}\n'
                    f'Email: {email}\n'
                    f'Expires: {oauth_token.expires_at}'
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f'OAuth token already exists for token: {token_key}'
                )
            )
