from django.apps import AppConfig


class AccountConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'account'
    label = 'pcheck_account'  # Unique label to avoid conflict with allauth.account
    
    def ready(self):
        """Import signals and ensure allauth providers are registered"""
        # Import here to avoid circular imports
        try:
            # Force import and registration of Google provider
            import allauth.socialaccount.providers.google
            from allauth.socialaccount.providers import registry
            from allauth.socialaccount.providers.google.provider import GoogleProvider
            # Ensure Google provider is registered
            if 'google' not in registry.provider_map:
                registry.register(GoogleProvider)
            
            # Connect signal for downloading Google profile pictures
            from allauth.socialaccount.models import SocialAccount
            from account.signals import download_google_profile_picture
            from django.db.models.signals import post_save
            
            # Connect the signal to download profile pictures when SocialAccount is saved
            post_save.connect(download_google_profile_picture, sender=SocialAccount, weak=False)
        except (ImportError, AttributeError):
            # Provider not available or already handled, skip
            pass
