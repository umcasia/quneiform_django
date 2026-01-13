# apps/form_builder/models.py
from django.db import models
from django.conf import settings
import json

class FormDraft(models.Model):
    DRAFT_TYPES = [
        ('auto_save', 'Auto Save'),
        ('manual', 'Manual'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    draft_name = models.CharField(max_length=255)
    draft_type = models.CharField(max_length=20, choices=DRAFT_TYPES, default='manual')
    
    # Form metadata
    form_name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=50)
    version = models.CharField(max_length=20, default='1')
    
    # Settings
    is_web = models.BooleanField(default=True)
    is_app = models.BooleanField(default=True)
    have_qc = models.BooleanField(default=True)
    have_validation = models.BooleanField(default=True)
    
    # Form schema (JSON)
    form_schema = models.JSONField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_drafts'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.draft_name} ({self.user.username})"
    
    @property
    def schema_json(self):
        return json.dumps(self.form_schema, indent=2)