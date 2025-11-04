from django import template

register = template.Library()

@register.filter
def has_profile(user):
    """Check if user has a profile"""
    try:
        return bool(user.profile)
    except:
        return False

@register.filter
def get_user_role(user):
    """Safely get user role from profile"""
    try:
        return user.profile.role
    except:
        return None
