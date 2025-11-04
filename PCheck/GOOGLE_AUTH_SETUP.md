# Google Authentication Setup Guide

This guide will help you set up Google OAuth2 authentication for the PCheck application.

## Prerequisites

1. A Google Cloud Platform account
2. Access to Google Cloud Console

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `django-allauth==0.62.0` which handles Google authentication.

## Step 2: Create Google OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google+ API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application"
   - Add authorized redirect URIs:
     - `http://127.0.0.1:8000/accounts/google/login/callback/` (development)
     - `http://localhost:8000/accounts/google/login/callback/` (development)
     - `https://yourdomain.com/accounts/google/login/callback/` (production)
   - Click "Create"
   - Copy the **Client ID** and **Client Secret**

## Step 3: Configure Django Settings

Open `PCheck/PCheckMain/settings.py` and update the Google OAuth settings:

```python
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'OAUTH_PKCE_ENABLED': True,
        'APP': {
            'client_id': 'YOUR_GOOGLE_CLIENT_ID',  # Replace with your Client ID
            'secret': 'YOUR_GOOGLE_CLIENT_SECRET',  # Replace with your Client Secret
            'key': ''
        }
    }
}
```

Replace `YOUR_GOOGLE_CLIENT_ID` and `YOUR_GOOGLE_CLIENT_SECRET` with your actual credentials.

## Step 4: Run Migrations

```bash
python manage.py migrate
```

This will create the necessary database tables for django-allauth.

## Step 5: Create a Site in Django Admin

1. Run the development server:
   ```bash
   python manage.py runserver
   ```
2. Go to http://127.0.0.1:8000/admin/
3. Navigate to "Sites" > "Sites"
4. Add or edit the default site:
   - Domain name: `127.0.0.1:8000` (for development) or your production domain
   - Display name: `PSU PCheck`

## Step 6: Add Google Social Application

1. In Django admin, go to "Social accounts" > "Social applications"
2. Click "Add social application"
3. Fill in the form:
   - Provider: `Google`
   - Name: `Google` (or any name you prefer)
   - Client id: Your Google Client ID
   - Secret key: Your Google Client Secret
   - Sites: Select your site (e.g., `127.0.0.1:8000`)
4. Click "Save"

## Step 7: Test the Integration

1. Start your Django server:
   ```bash
   python manage.py runserver
   ```
2. Navigate to the login page: http://127.0.0.1:8000/account/login/
3. Click "Sign in with Google"
4. You should be redirected to Google's login page
5. After successful authentication, you'll be redirected to the profile completion page

## How It Works

1. **User clicks "Sign in with Google"** → Redirected to Google OAuth
2. **User authenticates with Google** → Google redirects back to your app
3. **Profile completion** → If the user doesn't have a complete profile, they'll be asked to:
   - Select their role (Student/Faculty/Staff)
   - Select their college
   - Fill in additional details (course, year, block for students)
4. **Redirect** → User is redirected based on their role:
   - Staff → Dashboard
   - Student/Faculty → Home page

## Important Notes

- The system automatically extracts the `school_id` from PSU emails (`@psu.palawan.edu.ph`)
- For non-PSU emails, users can manually enter their school ID
- Profile completion is required before accessing the main application
- The system links existing accounts by email address

## Troubleshooting

### "Invalid redirect_uri" error
- Ensure the redirect URI in Google Cloud Console matches exactly:
  - Must include the trailing slash: `/accounts/google/login/callback/`
  - Must match the protocol (http vs https)
  - Must match the domain

### User not redirected to profile completion
- Check that the `CustomSocialAccountAdapter` is properly configured
- Verify `SOCIALACCOUNT_ADAPTER` setting in `settings.py`

### Profile not created
- Check Django signals in `account/signals.py`
- Verify the `save_user` method in `CustomSocialAccountAdapter`

## Production Considerations

1. **Update redirect URIs** in Google Cloud Console for your production domain
2. **Set `DEBUG = False`** in production settings
3. **Use environment variables** for sensitive credentials:
   ```python
   import os
   'client_id': os.environ.get('GOOGLE_CLIENT_ID'),
   'secret': os.environ.get('GOOGLE_CLIENT_SECRET'),
   ```
4. **Enable HTTPS** - Google requires HTTPS in production
5. **Update `ALLOWED_HOSTS`** with your production domain

