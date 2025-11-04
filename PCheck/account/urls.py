from django.urls import path
from django.contrib.auth import views as auth_views
from . import views as account_views

app_name = 'account'

urlpatterns = [
    path('login/', account_views.CustomLoginView.as_view(), name='login'),
    path('logout/', account_views.custom_logout_view, name='logout'),
    path('about/', account_views.about, name='about'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change_form.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),
    path('password-set/', account_views.password_set, name='password_set'),
    path('password-set/done/', account_views.password_set_done, name='password_set_done'),
    path('password-reset/', auth_views.PasswordResetView.as_view(),
        name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(),
        name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(),
        name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(),
        name='password_reset_complete'),
    path('register/', account_views.register, name='register'),
    path('verify/<email>/', account_views.verify, name='verify'),
    path('complete-profile/', account_views.complete_profile, name='complete-profile'),
    path('profile/', account_views.ProfileDetailView.as_view(), name='profile'),
    path('edit-profile/<int:pk>/', account_views.ProfileUpdateView.as_view(), name='edit-profile'),
]