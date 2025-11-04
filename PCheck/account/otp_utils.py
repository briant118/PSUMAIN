from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from account.models import OAuthToken
import random


def send_otp_email(email, user_name=None):
    """
    Generate and send OTP code via email
    Returns the OTP code for testing purposes
    """
    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    
    # Create OTP token in database
    oauth_token = OAuthToken.objects.create(
        otp_code=otp_code,
        user_email=email,
        is_active=True,
        expires_at=timezone.now() + timedelta(minutes=10)  # Expires in 10 minutes
    )
    
    # Prepare email context
    context = {
        'otp_code': otp_code,
        'email': email,
        'user_name': user_name or email.split('@')[0],
        'expiry_minutes': 10,
    }
    
    # Render email template
    html_message = render_to_string('account/otp_email.html', context)
    
    # Send email
    try:
        send_mail(
            subject='PSU PCheck Registration - OTP Code',
            message=f'Your PSU PCheck OTP code is: {otp_code}\n\nThis code expires in 10 minutes.\n\nIf you did not request this code, please ignore this email.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return {
            'success': True,
            'otp_code': otp_code,
            'message': f'OTP code sent successfully to {email}'
        }
        
    except Exception as e:
        # If email fails, still return the OTP for manual verification
        return {
            'success': False,
            'otp_code': otp_code,
            'message': f'Email sending failed: {str(e)}. OTP code: {otp_code}'
        }


def verify_otp_code(otp_code, email):
    """
    Verify OTP code for the given email
    Returns True if valid, False otherwise
    """
    try:
        oauth_obj = OAuthToken.objects.get(
            otp_code=otp_code,
            user_email=email,
            is_active=True
        )
        
        # Check if OTP is expired
        if oauth_obj.is_expired():
            return False
        
        # Deactivate the OTP after successful verification
        oauth_obj.is_active = False
        oauth_obj.save()
        
        return True
        
    except OAuthToken.DoesNotExist:
        return False
