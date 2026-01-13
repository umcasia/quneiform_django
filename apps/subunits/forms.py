# apps/subunits/forms.py
from django import forms
from .models import Subunit

class SubunitForm(forms.ModelForm):
    class Meta:
        model = Subunit
        fields = [
            'name',
            'acronym',
            'description',
            'active',
            'is_web',
            'is_app',
            'have_qc',
            'have_validation',
            'version',
            'view_home_map',
            'filter_home_map',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
