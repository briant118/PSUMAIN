from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
import requests
from .models import Profile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a User is created"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the Profile when the User is saved"""
    # Only update existing profile, don't create (create_user_profile handles creation)
    if kwargs.get('created', False):
        # New user - create_user_profile signal already created the profile
        return
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        # Profile doesn't exist - create it (shouldn't happen with create_user_profile signal)
        # Use get_or_create to avoid race conditions
        Profile.objects.get_or_create(user=instance)


# Signal to download Google profile picture when SocialAccount is saved
def download_google_profile_picture(sender, instance, created, **kwargs):
    """Download and save Google profile picture when SocialAccount is created/updated"""
    from allauth.socialaccount.models import SocialAccount
    
    # Only process Google accounts
    if not isinstance(instance, SocialAccount) or instance.provider != 'google':
        return
    
    # Get the user's profile
    try:
        profile = instance.user.profile
    except Profile.DoesNotExist:
        # Profile doesn't exist yet, create it
        profile = Profile.objects.create(user=instance.user)
    
    # Skip if profile picture already exists
    if profile.profile_picture:
        return
    
    # Get picture URL from extra_data
    if not instance.extra_data:
        return
    
    picture_url = instance.extra_data.get('picture')
    
    if not picture_url:
        return
    
    # Download the image
    try:
        response = requests.get(picture_url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Get file extension from URL or content-type
        ext = 'jpg'
        if '.' in picture_url:
            ext = picture_url.split('.')[-1].split('?')[0].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                ext = 'jpg'
        else:
            # Try to determine from content-type
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = 'png'
            elif 'gif' in content_type:
                ext = 'gif'
            elif 'webp' in content_type:
                ext = 'webp'
        
        # Create filename
        filename = f'profile_{instance.user.id}.{ext}'
        
        # Save to profile
        profile.profile_picture.save(
            filename,
            ContentFile(response.content),
            save=True
        )
    except (requests.RequestException, Exception) as e:
        # Silently fail if image download fails
        print(f"Failed to download Google profile picture: {e}")
        pass
