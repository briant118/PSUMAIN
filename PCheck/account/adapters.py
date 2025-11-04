from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
from django.urls import reverse
from . import models


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom adapter for regular account signups"""
    
    def get_login_redirect_url(self, request):
        """Redirect users after login based on profile completion"""
        user = request.user
        if hasattr(user, 'profile') and user.profile.role:
            # Profile is complete, redirect based on role
            if user.profile.role == 'staff':
                return reverse('account:dashboard')
            return '/'
        else:
            # Profile incomplete, redirect to completion
            return reverse('account:complete-profile')


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter for social account signups (Google, etc.)"""
    
    def is_open_for_signup(self, request, socialaccount):
        """Allow social account signups"""
        return True
    
    def populate_user(self, request, sociallogin, data):
        """Populate user fields from social account"""
        user = super().populate_user(request, sociallogin, data)
        
        # Get email domain to check if it's PSU email
        email = user.email
        if email and email.endswith('@psu.palawan.edu.ph'):
            # Extract school_id from email (e.g., john.doe@psu.palawan.edu.ph -> john.doe)
            school_id = email.split('@')[0]
            user.username = email
        else:
            # Use email as username if not PSU email
            user.username = email or f"user_{user.id}"
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Save user and create profile with Google profile picture"""
        user = super().save_user(request, sociallogin, form)
        
        # Create or get profile
        profile, created = models.Profile.objects.get_or_create(user=user)
        
        # Profile picture will be downloaded automatically via signal
        # when the SocialAccount is saved (see signals.py)
        
        return user
    
    def pre_social_login(self, request, sociallogin):
        """Called before social login"""
        # Check if user exists and link accounts
        user = sociallogin.user
        if user.id:
            # User already exists, skip
            return
        
        # Check if user with this email already exists
        try:
            existing_user = User.objects.get(email=user.email)
            # Link the social account to existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
    
    def get_connect_redirect_url(self, request, socialaccount):
        """Redirect after connecting social account"""
        user = request.user
        if hasattr(user, 'profile') and user.profile.role:
            if user.profile.role == 'staff':
                return reverse('account:dashboard')
            return '/'
        else:
            return reverse('account:complete-profile')
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Allow auto signup for Google users"""
        return True
    
    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        """Handle authentication errors"""
        # Redirect to login on error
        from django.shortcuts import redirect
        return redirect('account:login')
    
    def get_signup_redirect_url(self, request):
        """Redirect after social signup to profile completion"""
        user = request.user
        if hasattr(user, 'profile') and user.profile.role:
            # Profile already complete, redirect based on role
            if user.profile.role == 'staff':
                return reverse('account:dashboard')
            return '/'
        else:
            # Redirect to profile completion
            return reverse('account:complete-profile')

