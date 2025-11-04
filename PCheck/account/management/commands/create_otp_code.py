from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from account.models import OAuthToken


class Command(BaseCommand):
    help = 'Create OTP codes for user verification'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address for the OTP',
            required=True
        )
        parser.add_argument(
            '--otp',
            type=str,
            help='Specific OTP code (if not provided, will generate a random 6-digit code)',
            default=None
        )
        parser.add_argument(
            '--expiry-minutes',
            type=int,
            help='OTP expiry time in minutes (default: 10 minutes)',
            default=10
        )

    def handle(self, *args, **options):
        email = options['email']
        custom_otp = options['otp']
        expiry_minutes = options['expiry_minutes']
        
        # Generate OTP code
        if custom_otp:
            # Validate custom OTP format
            if not custom_otp.isdigit() or len(custom_otp) != 6:
                self.stdout.write(
                    self.style.ERROR(
                        'Custom OTP must be exactly 6 digits'
                    )
                )
                return
            otp_code = custom_otp
        else:
            # Generate random 6-digit OTP
            import random
            otp_code = str(random.randint(100000, 999999))
        
        # Create OTP token
        oauth_token = OAuthToken.objects.create(
            otp_code=otp_code,
            user_email=email,
            is_active=True,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes)
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created OTP code:\n'
                f'OTP Code: {otp_code}\n'
                f'Email: {email}\n'
                f'Expires: {oauth_token.expires_at}\n'
                f'Expiry Time: {expiry_minutes} minutes'
            )
        )
        
        # Display usage instructions
        self.stdout.write(
            self.style.WARNING(
                f'\nTo use this OTP:\n'
                f'1. Go to registration page\n'
                f'2. Complete registration with email: {email}\n'
                f'3. On OTP verification page, enter:\n'
                f'   - OTP Code: {otp_code}\n'
                f'   - Email: {email}'
            )
        )
