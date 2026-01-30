# services/form_builder_service.py
import json
import uuid
from django.db import models, connection
from django.apps import apps
from django.core.exceptions import ValidationError
from django.utils import timezone
from ..models import DynamicQuestion, SkipLogic, SkipLogicCondition, FieldValidation


class FormBuilderService:
    """Service to build forms from JSON schema"""
    
    def __init__(self, subunit):
        self.subunit = subunit
        self.schema = subunit.qnr_schema
        
    def build_form_structure(self):
        """Build form structure from schema"""
        try:
            # Clear existing questions
            DynamicQuestion.objects.filter(subunit=self.subunit).delete()
            
            # Process schema data
            sections = self.schema.get('data', [])
            for section in sections:
                self._process_section(section, None)
            
            return True
        except Exception as e:
            print(f"Error building form structure: {e}")
            return False
    
    def _process_section(self, section_data, parent_section):
        """Process a section and its children"""
        if section_data.get('type') != 'SECTION':
            return
        
        # Create section question
        section_question = DynamicQuestion.objects.create(
            subunit=self.subunit,
            question_id=section_data.get('acronym', str(uuid.uuid4())[:8]),
            question_type='SECTION',
            label=section_data.get('title', ''),
            properties=section_data,
            is_active=section_data.get('isActive', True),
            section=parent_section,
        )
        
        # Process children
        children = section_data.get('children', [])
        for child in children:
            if child.get('type') == 'SECTION':
                self._process_section(child, section_question)
            else:
                self._create_question(child, section_question)
    
    # services/form_builder_service.py - Update _create_question method
    def _create_question(self, question_data, section):
        """Create a question from schema data"""
        try:
            # Create question
            question = DynamicQuestion.objects.create(
                subunit=self.subunit,
                question_id=question_data.get('id', str(uuid.uuid4())[:8]),
                question_type=question_data.get('type'),
                label=question_data.get('properties', {}).get('label', ''),
                placeholder=question_data.get('properties', {}).get('placeholder', ''),
                q_number=question_data.get('properties', {}).get('qNumber', ''),
                properties=question_data.get('properties', {}),
                options=question_data.get('options', []),
                is_active=True,
                view_home=question_data.get('viewHome', False),
                filter_home=question_data.get('filterHome', False),
                primary_view=question_data.get('primaryView', False),
                secondary_view=question_data.get('secondaryView', False),
                view_index=question_data.get('viewIndex', 0),  # Default to 0 if not specified
                home_label=question_data.get('homeLabel', ''),
                section=section,
            )
            
            # Create validations
            self._create_validations(question, question_data.get('fieldValidations', {}))
            
            # Create skip logic
            self._create_skip_logic(question, question_data.get('skipLogic', []))
            
            return question
        except Exception as e:
            print(f"Error creating question: {e}")
            return None
    
    def _create_validations(self, question, validation_data):
        """Create validation rules for a question"""
        validations = []
        
        # Value required validation
        if validation_data.get('valueRequired'):
            validations.append({
                'validation_type': 'required',
                'value': 'true',
                'error_message': 'This field is required',
            })
        
        # Character length validations
        if 'minChar' in validation_data:
            validations.append({
                'validation_type': 'min_length',
                'value': str(validation_data['minChar']),
                'error_message': f'Minimum {validation_data["minChar"]} characters required',
            })
        
        if 'maxChar' in validation_data:
            validations.append({
                'validation_type': 'max_length',
                'value': str(validation_data['maxChar']),
                'error_message': f'Maximum {validation_data["maxChar"]} characters allowed',
            })
        
        # Multi-select validation
        if 'multiSelect' in validation_data:
            validations.append({
                'validation_type': 'multi_select',
                'value': str(validation_data['multiSelect']).lower(),
                'error_message': 'Invalid selection',
            })
        
        # Create validation records
        for validation in validations:
            FieldValidation.objects.create(
                question=question,
                **validation
            )
    
    def _create_skip_logic(self, question, skip_logic_data):
        """Create skip logic for a question"""
        for logic in skip_logic_data:
            skip_logic = SkipLogic.objects.create(
                question=question,
                relation=logic.get('relation', 'and'),
                flag=logic.get('flag', True),
                reverse_skip_logic=logic.get('reverseSkipLogic', False),
            )
            
            # Create conditions
            conditions = logic.get('data', [])
            for condition in conditions:
                SkipLogicCondition.objects.create(
                    skip_logic=skip_logic,
                    skip_logic_q=condition.get('skipLogicQ'),
                    skip_logic_val=condition.get('skipLogicVal'),
                    flag=condition.get('flag', True),
                )


class DynamicFormValidator:
    """Service to validate dynamic form data"""
    
    @staticmethod
    def validate_question_value(question, value):
        """Validate a single question value"""
        errors = []
        
        # Check if required
        if question.validations.filter(validation_type='required').exists():
            if not value or (isinstance(value, str) and value.strip() == ''):
                errors.append('This field is required')
        
        # Check character length for text fields
        if question.question_type in ['TEXT', 'TEXT_AREA'] and value:
            min_val = question.validations.filter(validation_type='min_length').first()
            max_val = question.validations.filter(validation_type='max_length').first()
            
            if min_val and len(str(value)) < int(min_val.value):
                errors.append(min_val.error_message)
            
            if max_val and len(str(value)) > int(max_val.value):
                errors.append(max_val.error_message)
        
        # Check dropdown/radio selection
        if question.question_type in ['DROPDOWN', 'RADIO']:
            if value and question.options:
                valid_options = [str(opt['id']) for opt in question.options]
                if value not in valid_options:
                    errors.append('Invalid selection')
        
        return errors
    
    @staticmethod
    def check_skip_logic(form_data, question):
        """Check if question should be shown based on skip logic"""
        skip_logics = question.skip_logic.all()
        
        for skip_logic in skip_logics:
            result = DynamicFormValidator._evaluate_skip_logic(skip_logic, form_data)
            
            # Apply reverse logic if needed
            if skip_logic.reverse_skip_logic:
                result = not result
            
            # If skip logic applies and flag is False (hide), return False
            if result and not skip_logic.flag:
                return False
        
        return True
    
    @staticmethod
    def _evaluate_skip_logic(skip_logic, form_data):
        """Evaluate skip logic conditions"""
        conditions = skip_logic.conditions.all()
        
        if skip_logic.relation == 'and':
            # All conditions must be true
            for condition in conditions:
                if not condition.flag:
                    continue
                
                field_value = form_data.get(condition.skip_logic_q)
                if field_value != condition.skip_logic_val:
                    return False
            return True
        
        elif skip_logic.relation == 'or':
            # At least one condition must be true
            for condition in conditions:
                if not condition.flag:
                    continue
                
                field_value = form_data.get(condition.skip_logic_q)
                if field_value == condition.skip_logic_val:
                    return True
            return False
        
        return True