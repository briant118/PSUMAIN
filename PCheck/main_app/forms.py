from django.contrib.auth.models import User
from django import forms
from . import models

class CreatePCForm(forms.ModelForm):
    class Meta:
        model = models.PC
        fields = '__all__'
        exclude = ['sort_number', 'booking_status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'ip_address': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control select'}),
            'system_condition': forms.Select(attrs={'class': 'form-control select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default status for new PCs (when no instance is provided)
        if not self.instance.pk:
            self.fields['status'].initial = 'connected'
            self.fields['system_condition'].initial = 'active'
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Set default booking_status for new PCs
        if not instance.pk:
            instance.booking_status = 'available'
        if commit:
            instance.save()
        return instance


class UpdatePCForm(forms.ModelForm):
    class Meta(CreatePCForm.Meta):
        fields = '__all__'

