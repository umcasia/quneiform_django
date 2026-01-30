# models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

from apps.subunits.models import Subunit

class SkipLogic(models.Model):
    """Model to store skip logic configuration"""
    LOGIC_RELATIONS = [
        ('and', 'AND'),
        ('or', 'OR'),
    ]
    
    question = models.ForeignKey('DynamicQuestion', on_delete=models.CASCADE, related_name='skip_logic')
    relation = models.CharField(max_length=10, choices=LOGIC_RELATIONS, default='and')
    flag = models.BooleanField(default=True)  # True = show, False = hide
    reverse_skip_logic = models.BooleanField(default=False)  # Reverse the logic
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'skip_logic'


class SkipLogicCondition(models.Model):
    """Individual conditions for skip logic"""
    skip_logic = models.ForeignKey(SkipLogic, on_delete=models.CASCADE, related_name='conditions')
    skip_logic_q = models.CharField(max_length=255)  # Question ID to check
    skip_logic_val = models.CharField(max_length=255)  # Value to compare
    flag = models.BooleanField(default=True)  # Whether this condition is active
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'skip_logic_conditions'


class FieldValidation(models.Model):
    """Model to store field validation rules"""
    VALIDATION_TYPES = [
        ('required', 'Required'),
        ('min_length', 'Minimum Length'),
        ('max_length', 'Maximum Length'),
        ('min_value', 'Minimum Value'),
        ('max_value', 'Maximum Value'),
        ('pattern', 'Regex Pattern'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('date_format', 'Date Format'),
        ('multi_select', 'Multiple Selection'),
        ('custom', 'Custom Validation'),
    ]
    
    question = models.ForeignKey(
        'DynamicQuestion',
        on_delete=models.CASCADE,
        related_name='validations'
    )
    # question = models.OneToOneField('DynamicQuestion', on_delete=models.CASCADE, related_name='validations')
    validation_type = models.CharField(max_length=50, choices=VALIDATION_TYPES)
    value = models.TextField(null=True, blank=True)  # Validation value (e.g., regex pattern, min value)
    error_message = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'field_validations'


class DynamicQuestion(models.Model):
    """Model to store question metadata"""
    QUESTION_TYPES = [
        ('TEXT', 'Text'),
        ('TEXT_AREA', 'Text Area'),
        ('NUMBER', 'Number'),
        ('DROPDOWN', 'Dropdown'),
        ('RADIO', 'Radio'),
        ('CHECKBOX', 'Checkbox'),
        ('DATE', 'Date'),
        ('TIME', 'Time'),
        ('DATETIME', 'Date Time'),
        ('UPLOAD_IMAGE', 'Upload Image'),
        ('UPLOAD_FILE', 'Upload File'),
        ('LOCATION', 'Location'),
        ('SIGNATURE', 'Signature'),
        ('RATING', 'Rating'),
        ('SECTION', 'Section'),
    ]
    
    subunit = models.ForeignKey('subunits.Subunit', on_delete=models.CASCADE, related_name='questions')
    question_id = models.CharField(max_length=255, unique=True)  # Unique ID from schema
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    label = models.TextField()
    placeholder = models.TextField(null=True, blank=True)
    q_number = models.CharField(max_length=50, null=True, blank=True)
    properties = models.JSONField(default=dict)  # Store all properties from schema
    options = models.JSONField(default=list, null=True, blank=True)  # For dropdown, radio, etc.
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    view_home = models.BooleanField(default=False)
    filter_home = models.BooleanField(default=False)
    primary_view = models.BooleanField(default=False)
    secondary_view = models.BooleanField(default=False)
    view_index = models.IntegerField(null=True, blank=True)
    home_label = models.CharField(max_length=255, null=True, blank=True)
    section = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dynamic_questions'
        ordering = ['view_index', 'created_at']
    
    def __str__(self):
        return f"{self.q_number}. {self.label[:50]}"


class FormSubmission(models.Model):
    """Model to track form submissions"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending_review', 'Pending Review'),
    ]
    
    subunit = models.ForeignKey('subunits.Subunit', on_delete=models.CASCADE, related_name='submissions')
    survey_id = models.CharField(max_length=100, unique=True)  # Generated survey ID
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='draft')
    submitted_data = models.JSONField(default=dict)  # All form data in JSON format
    metadata = models.JSONField(default=dict)  # Device info, location, etc.
    # submitted_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='submitted_by'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_submissions'
    )
    # reviewed_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_submissions')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'form_submissions'
        indexes = [
            models.Index(fields=['survey_id']),
            models.Index(fields=['status']),
            models.Index(fields=['submitted_at']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.survey_id:
            # Generate unique survey ID
            prefix = f"{self.subunit.acronym}"
            timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
            random_str = str(uuid.uuid4())[:8]
            self.survey_id = f"{prefix}_{timestamp}_{random_str}"
        super().save(*args, **kwargs)


class SubmissionData(models.Model):
    """Model to store individual submission data for each question"""
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='data')
    question = models.ForeignKey(DynamicQuestion, on_delete=models.CASCADE)
    table_name = models.CharField(max_length=255)  # Which dynamic table this belongs to
    field_name = models.CharField(max_length=255)  # Field name in the dynamic table
    value = models.TextField(null=True, blank=True)  # Text value
    file_value = models.FileField(upload_to='submissions/files/', null=True, blank=True)  # For files
    image_value = models.ImageField(upload_to='submissions/images/', null=True, blank=True)  # For images
    json_value = models.JSONField(null=True, blank=True)  # For JSON data
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'submission_data'
        unique_together = ['submission', 'question']
        indexes = [
            models.Index(fields=['submission', 'question']),
            models.Index(fields=['table_name', 'field_name']),
        ]