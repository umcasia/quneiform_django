# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from .models import Subunit, FormSubmission
from .services.form_builder_service import FormBuilderService, DynamicFormValidator
from .services.form_render_service import DynamicFormRenderer
from .services.form_submission_service import FormSubmissionService


@method_decorator(login_required, name='dispatch')
class DynamicFormView(View):
    """View to display and handle dynamic forms"""
    
    def get(self, request, subunit_id, submission_id=None):
        subunit = get_object_or_404(Subunit, id=subunit_id)
        
        # Build form structure if not exists
        if not subunit.questions.exists():
            FormBuilderService(subunit).build_form_structure()
        
        initial_data = {}
        submission = None
        
        # Load existing submission if provided
        if submission_id:
            submission = get_object_or_404(FormSubmission, id=submission_id, subunit=subunit)
            if submission.submitted_data:
                initial_data = submission.submitted_data
        
        # Create form class
        form_class = DynamicFormRenderer.create_form_class(subunit, initial_data)
        form = form_class(initial=initial_data)
        
        # Render form HTML with sections
        form_html = DynamicFormRenderer.render_form_with_sections(form)
        
        context = {
            'subunit': subunit,
            'form': form,
            'form_html': form_html,
            'submission': submission,
            'questions': subunit.questions.filter(is_active=True).order_by('view_index'),
        }
        
        return render(request, 'dynamic_form.html', context)


    # views.py - Update the POST method
    def post(self, request, subunit_id, submission_id=None):
        subunit = get_object_or_404(Subunit, id=subunit_id)
        
        # Check if this is a draft save
        save_as_draft = request.POST.get('save_as_draft') == 'true'
        
        # Build form structure if not exists
        if not subunit.questions.exists():
            FormBuilderService(subunit).build_form_structure()
        
        # Create form instance
        form_class = DynamicFormRenderer.create_form_class(subunit)
        
        # Handle both AJAX and regular form submissions
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and save_as_draft:
            form = form_class(request.POST, request.FILES)
            
            if form.is_valid():
                try:
                    # Save as draft
                    submission_service = FormSubmissionService(subunit, request.user)
                    metadata = {
                        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                        'ip_address': request.META.get('REMOTE_ADDR', ''),
                        'submitted_via': 'web_draft',
                    }
                    
                    if submission_id:
                        submission = get_object_or_404(FormSubmission, id=submission_id)
                        submission.submitted_data = form.cleaned_data
                        submission.metadata.update(metadata)
                        submission.status = 'draft'
                        submission.save()
                    else:
                        submission = submission_service.submit_form(form.cleaned_data, metadata)
                        submission.status = 'draft'
                        submission.save()
                    
                    return JsonResponse({
                        'success': True,
                        'submission_id': submission.id,
                        'message': 'Draft saved successfully'
                    })
                    
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Form validation failed',
                    'errors': form.errors
                })
        
        # Regular form submission
        form = form_class(request.POST, request.FILES)
        
        if form.is_valid():
            # Apply skip logic validation
            form_data = form.cleaned_data
            questions = subunit.questions.filter(is_active=True)
            
            # Validate each question based on skip logic
            for question in questions:
                should_show = DynamicFormValidator.check_skip_logic(form_data, question)
                
                if not should_show:
                    # Remove field from validation if hidden by skip logic
                    if question.question_id in form_data:
                        del form_data[question.question_id]
                else:
                    # Validate field value
                    value = form_data.get(question.question_id)
                    errors = DynamicFormValidator.validate_question_value(question, value)
                    
                    if errors:
                        for error in errors:
                            form.add_error(question.question_id, error)
            
            if not form.errors:
                # Save submission
                submission_service = FormSubmissionService(subunit, request.user)
                
                # Prepare metadata
                metadata = {
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'ip_address': request.META.get('REMOTE_ADDR', ''),
                    'submitted_via': 'web',
                }
                
                try:
                    if submission_id:
                        # Update existing submission
                        submission = get_object_or_404(FormSubmission, id=submission_id)
                        submission.submitted_data = form_data
                        submission.metadata.update(metadata)
                        submission.status = 'submitted'
                        submission.submitted_at = timezone.now()
                        submission.save()
                    else:
                        # Create new submission
                        submission = submission_service.submit_form(form_data, metadata)
                    
                    messages.success(request, 'Form submitted successfully!')
                    return redirect('forms:submission_detail', submission_id=submission.id)
                    
                except Exception as e:
                    messages.error(request, f'Error saving form: {str(e)}')
        
        # If form is invalid, render with errors
        form_html = DynamicFormRenderer.render_form_with_sections(form)
        
        context = {
            'subunit': subunit,
            'form': form,
            'form_html': form_html,
            'questions': subunit.questions.filter(is_active=True).order_by('view_index'),
        }
        
        return render(request, 'dynamic_form.html', context)


@method_decorator(login_required, name='dispatch')
class FormSubmissionListView(View):
    """View to list form submissions"""
    
    def get(self, request, subunit_id):
        subunit = get_object_or_404(Subunit, id=subunit_id)
        
        submissions = FormSubmission.objects.filter(
            subunit=subunit
        ).order_by('-created_at')
        
        context = {
            'subunit': subunit,
            'submissions': submissions,
        }
        
        return render(request, 'submission_list.html', context)


@method_decorator(login_required, name='dispatch')
class FormSubmissionDetailView(View):
    """View to display submission details"""
    
    def get(self, request, submission_id):
        submission = get_object_or_404(FormSubmission, id=submission_id)
        
        # Get submission data
        submission_service = FormSubmissionService(submission.subunit)
        submission_data = submission_service.get_form_data(submission.id)
        
        context = {
            'submission': submission,
            'form_data': submission_data['form_data'],
            'submission_data': submission_data['submission_data'],
        }
        
        return render(request, 'submission_detail.html', context)


class FormDataAPIView(View):
    """API endpoint to get form data"""
    
    def get(self, request, subunit_id):
        subunit = get_object_or_404(Subunit, id=subunit_id)
        
        # Get all questions with their properties
        questions = DynamicQuestion.objects.filter(
            subunit=subunit,
            is_active=True
        ).values(
            'question_id',
            'question_type',
            'label',
            'placeholder',
            'q_number',
            'options',
            'is_required',
            'view_home',
            'filter_home',
            'view_index',
            'home_label',
        ).order_by('view_index')
        
        # Get skip logic data
        skip_logic_data = {}
        for question in subunit.questions.all():
            skip_logic = []
            for sl in question.skip_logic.all():
                conditions = list(sl.conditions.values('skip_logic_q', 'skip_logic_val', 'flag'))
                skip_logic.append({
                    'relation': sl.relation,
                    'flag': sl.flag,
                    'reverse_skip_logic': sl.reverse_skip_logic,
                    'conditions': conditions,
                })
            
            if skip_logic:
                skip_logic_data[question.question_id] = skip_logic
        
        response_data = {
            'questions': list(questions),
            'skip_logic': skip_logic_data,
            'subunit': {
                'id': subunit.id,
                'name': subunit.name,
                'acronym': subunit.acronym,
            }
        }
        
        return JsonResponse(response_data)