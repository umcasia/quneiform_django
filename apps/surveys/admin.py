# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import DynamicQuestion, SkipLogic, FieldValidation, FormSubmission, SubmissionData


@admin.register(DynamicQuestion)
class DynamicQuestionAdmin(admin.ModelAdmin):
    list_display = ['q_number', 'label', 'question_type', 'subunit', 'is_active', 'view_index']
    list_filter = ['question_type', 'is_active', 'subunit']
    search_fields = ['label', 'question_id', 'q_number']
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 20
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('subunit', 'question_id', 'question_type', 'label', 'placeholder', 'q_number')
        }),
        ('Display Settings', {
            'fields': ('view_home', 'filter_home', 'primary_view', 'secondary_view', 'view_index', 'home_label')
        }),
        ('Properties', {
            'fields': ('properties', 'options', 'is_required', 'is_active', 'section')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['survey_id', 'subunit', 'status', 'submitted_by', 'submitted_at']
    list_filter = ['status', 'subunit', 'submitted_at']
    search_fields = ['survey_id', 'submitted_data']
    readonly_fields = ['created_at', 'updated_at', 'survey_id']
    list_per_page = 20
    
    def view_submission_link(self, obj):
        return format_html('<a href="/admin/forms/submission/{}/change/">View Details</a>', obj.id)
    
    view_submission_link.short_description = 'Action'


@admin.register(SkipLogic)
class SkipLogicAdmin(admin.ModelAdmin):
    list_display = ['question', 'relation', 'flag', 'reverse_skip_logic']
    list_filter = ['relation', 'flag']
    search_fields = ['question__label', 'question__question_id']


@admin.register(FieldValidation)
class FieldValidationAdmin(admin.ModelAdmin):
    list_display = ['question', 'validation_type', 'value', 'is_active']
    list_filter = ['validation_type', 'is_active']
    search_fields = ['question__label', 'error_message']