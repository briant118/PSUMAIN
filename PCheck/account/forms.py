from django import forms
from django.contrib.auth.models import User
from . import models


class PrefixLoginForm(forms.Form):
    username = forms.CharField(
        label="Email Prefix", max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your school ID', 'required': 'required'})
        )
    password = forms.CharField(widget=forms.PasswordInput)


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'required': 'required'}))

    
class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Repeat password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['email',]
        widgets = {
            'username': forms.TextInput(attrs={'hidden': 'hidden'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError("Passwords don't match.")
        return cd['password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = models.Profile
        fields = ['college', 'course', 'year', 'block', 'profile_picture']
        widgets = {
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class UpdatePCForm(forms.ModelForm):
    class Meta(ProfileEditForm.Meta):
        fields = '__all__'