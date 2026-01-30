# services/form_submission_service.py
import uuid
import json
from django.db import transaction, models, connection
from django.apps import apps
from django.utils import timezone
from django.core.files.base import ContentFile
from ..models import FormSubmission, SubmissionData, DynamicQuestion


class FormSubmissionService:
    """Service to handle form submissions"""
    
    def __init__(self, subunit, user=None):
        self.subunit = subunit
        self.user = user
    
    @transaction.atomic
    def submit_form(self, form_data, metadata=None):
        """Submit form data"""
        try:
            # Create submission record
            submission = FormSubmission.objects.create(
                subunit=self.subunit,
                submitted_data=form_data,
                metadata=metadata or {},
                submitted_by=self.user,
                submitted_at=timezone.now(),
                status='submitted',
            )
            
            # Process and save data
            self._save_submission_data(submission, form_data)
            
            return submission
        except Exception as e:
            print(f"Error submitting form: {e}")
            raise
    
    def _save_submission_data(self, submission, form_data):
        """Save submission data to appropriate tables"""
        # Get all questions for this subunit
        questions = DynamicQuestion.objects.filter(
            subunit=self.subunit,
            is_active=True
        ).select_related('section')
        
        # Group data by table
        table_data = {}
        
        for question in questions:
            field_name = question.question_id
            field_value = form_data.get(field_name)
            
            if field_value is None:
                continue
            
            # Determine which table this belongs to
            table_name = self._get_table_name_for_question(question)
            
            if table_name not in table_data:
                table_data[table_name] = {}
            
            table_data[table_name][field_name] = field_value
            
            # Save to SubmissionData for reference
            self._save_to_submission_data(submission, question, table_name, field_value)
        
        # Save to dynamic tables
        self._save_to_dynamic_tables(submission, table_data)
    
    def _get_table_name_for_question(self, question):
        """Determine which dynamic table a question belongs to"""
        # Traverse up to find the section
        current = question
        acronyms = []
        
        while current and current.section:
            acronyms.insert(0, current.section.question_id)
            current = current.section
        
        # Get project acronym and subunit acronym
        project_acronym = self.subunit.project.acronym
        subunit_acronym = self.subunit.acronym
        
        if acronyms:
            # Nested section
            parent_table = f"{project_acronym}_{subunit_acronym}_{acronyms[0]}"
            for i in range(1, len(acronyms)):
                parent_table = f"{parent_table}_{acronyms[i]}"
            return parent_table
        else:
            # Top-level section
            return f"{project_acronym}_{subunit_acronym}_{question.section.question_id if question.section else 'MAIN'}"
    
    def _save_to_submission_data(self, submission, question, table_name, value):
        """Save individual question data to SubmissionData"""
        submission_data = SubmissionData(
            submission=submission,
            question=question,
            table_name=table_name,
            field_name=question.question_id,
        )
        
        # Store value based on type
        if question.question_type in ['UPLOAD_IMAGE', 'UPLOAD_FILE']:
            # Handle file uploads
            if isinstance(value, dict) and 'file' in value:
                # This would need actual file handling
                pass
            else:
                submission_data.json_value = value
        elif isinstance(value, (dict, list)):
            submission_data.json_value = value
        else:
            submission_data.value = str(value)
        
        submission_data.save()
    
    def _save_to_dynamic_tables(self, submission, table_data):
        """Save data to dynamic tables"""
        with connection.cursor() as cursor:
            for table_name, data in table_data.items():
                if not data:
                    continue
                
                # Prepare columns and values
                columns = ['ss_id'] + list(data.keys())
                values = [submission.id] + list(data.values())
                
                # Escape values for SQL
                escaped_values = []
                for val in values:
                    if val is None:
                        escaped_values.append('NULL')
                    elif isinstance(val, (int, float)):
                        escaped_values.append(str(val))
                    else:
                        escaped_values.append(f"'{str(val).replace("'", "''")}'")
                
                # Build and execute SQL
                columns_str = ', '.join([f'"{col}"' for col in columns])
                values_str = ', '.join(escaped_values)
                
                sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({values_str})'
                cursor.execute(sql)
    
    def get_form_data(self, submission_id):
        """Retrieve form data for a submission"""
        submission = FormSubmission.objects.get(id=submission_id)
        
        # Get all submission data
        submission_data = SubmissionData.objects.filter(
            submission=submission
        ).select_related('question')
        
        # Reconstruct form data
        form_data = {}
        for data in submission_data:
            if data.json_value is not None:
                form_data[data.field_name] = data.json_value
            elif data.file_value:
                form_data[data.field_name] = data.file_value.url
            elif data.image_value:
                form_data[data.field_name] = data.image_value.url
            else:
                form_data[data.field_name] = data.value
        
        return {
            'submission': submission,
            'form_data': form_data,
            'submission_data': submission_data,
        }