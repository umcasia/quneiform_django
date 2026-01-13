# apps/form_builder/forms.py
from django import forms
from .models import FormDraft

class FormDraftForm(forms.ModelForm):
    class Meta:
        model = FormDraft
        fields = ['draft_name', 'form_name', 'acronym', 'version']
        widgets = {
            'draft_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter draft name'
            }),
            'form_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Waste Pickers Survey'
            }),
            'acronym': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Form acronym'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1.0.0'
            }),
        }