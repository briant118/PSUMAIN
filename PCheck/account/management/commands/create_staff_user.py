from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from account.models import Profile, College


class Command(BaseCommand):
    help = 'Create a staff user for testing'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, default='staff', help='Username for staff user')
        parser.add_argument('--email', type=str, default='staff@psu.palawan.edu.ph', help='Email for staff user')
        parser.add_argument('--password', type=str, default='staff123', help='Password for staff user')
        parser.add_argument('--first-name', type=str, default='Staff', help='First name')
        parser.add_argument('--last-name', type=str, default='User', help='Last name')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Create or get user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'is_staff': True,
            }
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created staff user: {username}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Staff user already exists: {username}')
            )

        # Create or update profile
        try:
            profile = user.profile
            profile.role = 'staff'
            profile.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated profile for user: {username}')
            )
        except Profile.DoesNotExist:
            # Get or create a default college
            college, _ = College.objects.get_or_create(
                name='Default College',
                defaults={'description': 'Default college for staff users'}
            )
            
            profile = Profile.objects.create(
                user=user,
                role='staff',
                college=college,
                school_id=username
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created profile for user: {username}')
            )

        self.stdout.write(
            self.style.SUCCESS(f'Staff user setup complete!')
        )
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'Login URL: /account/staff-login/')
