# services/form_render_service.py
from django import forms
from django.utils.safestring import mark_safe
import json
from collections import defaultdict
from ..models import DynamicQuestion, FieldValidation


class DynamicFormRenderer:
    """Service to render dynamic forms with proper sections"""
    
    @staticmethod
    def create_form_class(subunit, initial_data=None):
        """Create a Django Form class from dynamic questions"""
        form_fields = {}
        
        # Get all active questions in correct order
        questions = DynamicQuestion.objects.filter(
            subunit=subunit,
            is_active=True
        ).order_by('view_index', 'created_at')
        
        for question in questions:
            field = DynamicFormRenderer._create_form_field(question, initial_data)
            if field:
                form_fields[question.question_id] = field
        
        # Create form class
        form_class = type('DynamicForm', (forms.Form,), form_fields)
        
        # Add custom methods
        form_class.get_questions = lambda self: questions
        form_class.get_question_by_id = lambda self, qid: questions.filter(question_id=qid).first()
        
        return form_class
    
    @staticmethod
    def _create_form_field(question, initial_data):
        """Create a Django form field from question"""
        initial_value = initial_data.get(question.question_id) if initial_data else None
        
        # Include question number in label
        label = f"{question.q_number}. {question.label}" if question.q_number else question.label
        
        # Determine field class based on question type
        if question.question_type == 'TEXT':
            field = forms.CharField(
                label=mark_safe(label),
                initial=initial_value,
                required=question.validations.filter(validation_type='required').exists(),
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': question.placeholder or '',
                    'data-question-id': question.question_id,
                    'data-q-number': question.q_number or '',
                })
            )
        
        elif question.question_type == 'DROPDOWN':
            choices = [(opt['id'], opt['value']) for opt in question.options]
            
            # Check if multi-select
            multi_select = question.validations.filter(
                validation_type='multi_select',
                value='true'
            ).exists()
            
            if multi_select:
                field = forms.MultipleChoiceField(
                    label=mark_safe(label),
                    choices=choices,
                    initial=initial_value,
                    required=question.validations.filter(validation_type='required').exists(),
                    widget=forms.SelectMultiple(attrs={
                        'class': 'form-control',
                        'data-question-id': question.question_id,
                        'data-q-number': question.q_number or '',
                    })
                )
            else:
                field = forms.ChoiceField(
                    label=mark_safe(label),
                    choices=choices,
                    initial=initial_value,
                    required=question.validations.filter(validation_type='required').exists(),
                    widget=forms.Select(attrs={
                        'class': 'form-control',
                        'placeholder': question.placeholder or '',
                        'data-question-id': question.question_id,
                        'data-q-number': question.q_number or '',
                    })
                )
        
        elif question.question_type == 'RADIO':
            choices = [(opt['id'], opt['value']) for opt in question.options]
            field = forms.ChoiceField(
                label=mark_safe(label),
                choices=choices,
                initial=initial_value,
                required=question.validations.filter(validation_type='required').exists(),
                widget=forms.RadioSelect(attrs={
                    'data-question-id': question.question_id,
                    'data-q-number': question.q_number or '',
                })
            )
        
        elif question.question_type == 'UPLOAD_IMAGE':
            field = forms.ImageField(
                label=mark_safe(label),
                required=question.validations.filter(validation_type='required').exists(),
                widget=forms.FileInput(attrs={
                    'class': 'form-control',
                    'accept': 'image/*',
                    'data-question-id': question.question_id,
                    'data-q-number': question.q_number or '',
                })
            )
        
        elif question.question_type == 'TEXT_AREA':
            max_length = None
            min_length = None
            
            for validation in question.validations.all():
                if validation.validation_type == 'max_length':
                    max_length = int(validation.value)
                elif validation.validation_type == 'min_length':
                    min_length = int(validation.value)
            
            field = forms.CharField(
                label=mark_safe(label),
                initial=initial_value,
                required=question.validations.filter(validation_type='required').exists(),
                max_length=max_length,
                min_length=min_length,
                widget=forms.Textarea(attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': question.placeholder or '',
                    'data-question-id': question.question_id,
                    'data-q-number': question.q_number or '',
                })
            )
        
        elif question.question_type == 'DATE':
            field = forms.DateField(
                label=mark_safe(label),
                initial=initial_value,
                required=question.validations.filter(validation_type='required').exists(),
                widget=forms.DateInput(
                    format='%Y-%m-%d',
                    attrs={
                        'class': 'form-control datepicker',
                        'type': 'date',
                        'data-question-id': question.question_id,
                        'data-q-number': question.q_number or '',
                    }
                )
            )
        
        else:
            # Default text field for unknown types
            field = forms.CharField(
                label=mark_safe(label),
                initial=initial_value,
                required=question.validations.filter(validation_type='required').exists(),
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': question.placeholder or '',
                    'data-question-id': question.question_id,
                    'data-q-number': question.q_number or '',
                })
            )
        
        return field
    
    @staticmethod
    def render_form_with_sections(form, include_js=True):
        """Render form with sections as tabs and subsections as accordions"""
        # Get all sections and questions organized hierarchically
        sections = DynamicFormRenderer._build_section_hierarchy(form)
        
        html_parts = []
        
        # If we have multiple top-level sections, use tabs
        if len(sections) > 1:
            html_parts.append(DynamicFormRenderer._render_tabs(sections))
            html_parts.append(DynamicFormRenderer._render_tab_content(form, sections))
        else:
            # Single section - render without tabs
            html_parts.append(DynamicFormRenderer._render_single_section(form, sections[0]))
        
        # Add JavaScript for skip logic if needed
        if include_js:
            js_html = DynamicFormRenderer._generate_skip_logic_js(form)
            html_parts.append(js_html)
        
        return mark_safe('\n'.join(html_parts))
    
    @staticmethod
    def _build_section_hierarchy(form):
        """Build hierarchical structure of sections and questions"""
        questions = form.get_questions()
        
        # Organize by section
        sections_dict = defaultdict(lambda: {'section': None, 'questions': [], 'subsections': defaultdict(lambda: {'questions': []})})
        
        for question in questions:
            section = question.section
            
            if not section:
                # This is a top-level question (shouldn't happen in our schema)
                continue
            
            # Get section acronym from properties
            section_acronym = section.properties.get('acronym', '')
            section_title = section.properties.get('title', 'Untitled Section')
            
            # Get subsection if exists (nested sections)
            parent_section = section.section
            
            if parent_section:
                # This is a subsection
                parent_acronym = parent_section.properties.get('acronym', '')
                sections_dict[parent_acronym]['subsections'][section_acronym]['questions'].append(question)
            else:
                # This is a top-level section
                sections_dict[section_acronym]['section'] = section
                sections_dict[section_acronym]['questions'].append(question)
        
        # Convert to list structure
        sections_list = []
        for acronym, data in sections_dict.items():
            if data['section']:
                section_data = {
                    'acronym': acronym,
                    'title': data['section'].properties.get('title', ''),
                    'questions': data['questions'],
                    'subsections': []
                }
                
                # Add subsections
                for sub_acronym, sub_data in data['subsections'].items():
                    # Find subsection in questions
                    subsection_q = [q for q in questions if q.section and 
                                   q.section.properties.get('acronym') == sub_acronym and
                                   q.section.section == data['section']]
                    if subsection_q:
                        section_data['subsections'].append({
                            'acronym': sub_acronym,
                            'title': subsection_q[0].section.properties.get('title', ''),
                            'questions': sub_data['questions']
                        })
                
                sections_list.append(section_data)
        
        # Sort sections by view_index or creation order
        return sorted(sections_list, key=lambda x: getattr(x.get('section', None), 'view_index', 0))
    
    @staticmethod
    def _render_tabs(sections):
        """Render Bootstrap 5 tabs navigation"""
        html_parts = ['<ul class="nav nav-tabs mb-3" id="formTabs" role="tablist">']
        
        for idx, section in enumerate(sections):
            active = 'active' if idx == 0 else ''
            section_id = section['acronym'].lower().replace(' ', '-')
            
            html_parts.append(f'''
            <li class="nav-item" role="presentation">
                <button class="nav-link {active}" 
                        id="tab-{section_id}" 
                        data-bs-toggle="tab" 
                        data-bs-target="#pane-{section_id}" 
                        type="button" 
                        role="tab" 
                        aria-controls="pane-{section_id}"
                        aria-selected="{'true' if idx == 0 else 'false'}">
                    {section['title']}
                </button>
            </li>
            ''')
        
        html_parts.append('</ul>')
        return '\n'.join(html_parts)
    
    @staticmethod
    def _render_tab_content(form, sections):
        """Render tab content with sections and subsections"""
        html_parts = ['<div class="tab-content" id="formTabsContent">']
        
        for idx, section in enumerate(sections):
            active = 'show active' if idx == 0 else ''
            section_id = section['acronym'].lower().replace(' ', '-')
            
            html_parts.append(f'''
            <div class="tab-pane fade {active}" 
                 id="pane-{section_id}" 
                 role="tabpanel" 
                 aria-labelledby="tab-{section_id}"
                 tabindex="0">
            ''')
            
            # Render section questions and subsections
            html_parts.append(DynamicFormRenderer._render_section_content(form, section))
            
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    @staticmethod
    def _render_single_section(form, section):
        """Render a single section without tabs"""
        html_parts = []
        html_parts.append(f'<div class="single-section">')
        html_parts.append(DynamicFormRenderer._render_section_content(form, section))
        html_parts.append('</div>')
        return '\n'.join(html_parts)
    
    @staticmethod
    def _render_section_content(form, section):
        """Render section content with questions and subsections as accordions"""
        html_parts = []
        
        # Section header
        html_parts.append(f'<h4 class="section-title mb-4">{section["title"]}</h4>')
        
        # Render questions in this section
        for question in section['questions']:
            field = form[question.question_id]
            field_html = DynamicFormRenderer._render_field_html(field, question)
            html_parts.append(field_html)
        
        # Render subsections as accordions
        if section.get('subsections'):
            accordion_id = f"accordion-{section['acronym']}"
            html_parts.append(f'<div class="accordion mt-4" id="{accordion_id}">')
            
            for sub_idx, subsection in enumerate(section['subsections']):
                accordion_item_id = f"{accordion_id}-item-{sub_idx}"
                
                html_parts.append(f'''
                <div class="accordion-item">
                    <h2 class="accordion-header" id="{accordion_item_id}-header">
                        <button class="accordion-button collapsed" 
                                type="button" 
                                data-bs-toggle="collapse" 
                                data-bs-target="#{accordion_item_id}-body" 
                                aria-expanded="false" 
                                aria-controls="{accordion_item_id}-body">
                            {subsection['title']}
                        </button>
                    </h2>
                    <div id="{accordion_item_id}-body" 
                         class="accordion-collapse collapse" 
                         aria-labelledby="{accordion_item_id}-header" 
                         data-bs-parent="#{accordion_id}">
                        <div class="accordion-body">
                ''')
                
                # Render subsection questions
                for question in subsection['questions']:
                    field = form[question.question_id]
                    field_html = DynamicFormRenderer._render_field_html(field, question)
                    html_parts.append(field_html)
                
                html_parts.append('''
                        </div>
                    </div>
                </div>
                ''')
            
            html_parts.append('</div>')
        
        return '\n'.join(html_parts)
    
    @staticmethod
    def _render_field_html(field, question):
        """Render individual field HTML with question number"""
        # Get question number from q_number or use default
        q_number = question.q_number or ''
        
        field_html = f"""
        <div class="form-group question-field mb-3" 
             data-question-id="{question.question_id}"
             data-field-type="{question.question_type}"
             data-q-number="{q_number}">
            <label for="{field.id_for_label}" class="form-label">
                <span class="question-number">{q_number}</span>. {field.label}
                {'' if not field.field.required else '<span class="text-danger">*</span>'}
            </label>
            {field}
            {field.errors}
            <div class="form-text text-muted">{field.help_text or ''}</div>
        </div>
        """
        return field_html
    
    @staticmethod
    def _generate_skip_logic_js(form):
        """Generate JavaScript for skip logic"""
        skip_logic_data = []
        
        for question in form.get_questions():
            for skip_logic in question.skip_logic.all():
                conditions = []
                for condition in skip_logic.conditions.all():
                    conditions.append({
                        'question_id': condition.skip_logic_q,
                        'value': condition.skip_logic_val,
                        'flag': condition.flag,
                    })
                
                skip_logic_data.append({
                    'target_question': question.question_id,
                    'relation': skip_logic.relation,
                    'flag': skip_logic.flag,
                    'reverse': skip_logic.reverse_skip_logic,
                    'conditions': conditions,
                })
        
        js = f"""
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const skipLogicData = {json.dumps(skip_logic_data)};
            
            // Function to evaluate skip logic
            function evaluateSkipLogic(logic, formValues) {{
                let results = logic.conditions.map(condition => {{
                    const value = formValues[condition.question_id];
                    const matches = value == condition.value;
                    return condition.flag ? matches : !matches;
                }});
                
                if (logic.relation === 'and') {{
                    return results.every(r => r);
                }} else {{
                    return results.some(r => r);
                }}
            }}
            
            // Function to update field visibility
            function updateFieldVisibility() {{
                const formValues = {{}};
                
                // Collect current form values
                document.querySelectorAll('.question-field input, .question-field select, .question-field textarea').forEach(el => {{
                    const questionId = el.closest('.question-field').dataset.questionId;
                    if (el.type === 'checkbox' || el.type === 'radio') {{
                        formValues[questionId] = document.querySelector(`input[name="${{el.name}}"]:checked`)?.value;
                    }} else {{
                        formValues[questionId] = el.value;
                    }}
                }});
                
                // Apply skip logic
                skipLogicData.forEach(logic => {{
                    const shouldShow = evaluateSkipLogic(logic, formValues);
                    const targetElement = document.querySelector(`[data-question-id="${{logic.target_question}}"]`);
                    
                    if (targetElement) {{
                        if (shouldShow && logic.flag) {{
                            targetElement.style.display = 'block';
                        }} else {{
                            targetElement.style.display = 'none';
                            // Clear value when hidden
                            const input = targetElement.querySelector('input, select, textarea');
                            if (input) {{
                                input.value = '';
                                // Trigger change event
                                input.dispatchEvent(new Event('change'));
                            }}
                        }}
                    }}
                }});
            }}
            
            // Attach event listeners
            document.querySelectorAll('input, select, textarea').forEach(el => {{
                el.addEventListener('change', updateFieldVisibility);
                el.addEventListener('input', updateFieldVisibility);
            }});
            
            // Initial update
            updateFieldVisibility();
        }});
        </script>
        """
        return mark_safe(js)