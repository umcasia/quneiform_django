# apps/form_builder/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
import json
from .models import FormDraft
from apps.subunits.models import Subunit
from apps.projects.models import Project

@login_required
@permission_required('subunits.manage_subunit', raise_exception=True)
def form_builder(request, project_id, subunit_id=None):
    project = get_object_or_404(Project, id=project_id)
    
    context = {
        'project': project,
        'subunit': None,
        'user': request.user,
    }
    
    if subunit_id:
        subunit = get_object_or_404(Subunit, id=subunit_id, project=project)
        context['subunit'] = subunit
    
    return render(request, 'form_builder.html', context)

@login_required
@require_POST
def save_draft(request):
    try:
        data = json.loads(request.body)
        
        draft = FormDraft.objects.create(
            user=request.user,
            draft_name=data.get('draft_name', 'Untitled Draft'),
            draft_type='manual',
            form_name=data.get('form_name', ''),
            acronym=data.get('acronym', ''),
            version=data.get('version', '1'),
            is_web=data.get('is_web', True),
            is_app=data.get('is_app', True),
            have_qc=data.get('have_qc', True),
            have_validation=data.get('have_validation', True),
            form_schema=data.get('form_schema', {})
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Draft saved successfully',
            'draft_id': draft.id
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving draft: {str(e)}'
        }, status=400)

@login_required
@require_POST
def auto_save_draft(request):
    try:
        data = json.loads(request.body)
        
        # Get or create auto-save draft
        draft, created = FormDraft.objects.update_or_create(
            user=request.user,
            draft_type='auto_save',
            defaults={
                'draft_name': 'Auto-saved Draft',
                'form_name': data.get('form_name', 'Auto-saved Survey'),
                'acronym': data.get('acronym', ''),
                'version': data.get('version', '1'),
                'is_web': data.get('is_web', True),
                'is_app': data.get('is_app', True),
                'have_qc': data.get('have_qc', True),
                'have_validation': data.get('have_validation', True),
                'form_schema': data.get('form_schema', {})
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Auto-saved successfully',
            'timestamp': draft.updated_at.isoformat()
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Auto-save failed: {str(e)}'
        }, status=400)

@login_required
@require_GET
def get_auto_save_draft(request):
    try:
        draft = FormDraft.objects.filter(
            user=request.user,
            draft_type='auto_save'
        ).first()
        
        if draft:
            return JsonResponse({
                'success': True,
                'exists': True,
                'draft': {
                    'id': draft.id,
                    'form_name': draft.form_name,
                    'acronym': draft.acronym,
                    'version': draft.version,
                    'is_web': draft.is_web,
                    'is_app': draft.is_app,
                    'have_qc': draft.have_qc,
                    'have_validation': draft.have_validation,
                    'form_schema': draft.form_schema,
                    'updated_at': draft.updated_at.isoformat()
                }
            })
        
        return JsonResponse({
            'success': True,
            'exists': False
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error getting draft: {str(e)}'
        }, status=400)

@login_required
@require_POST
def delete_auto_save_draft(request):
    try:
        FormDraft.objects.filter(
            user=request.user,
            draft_type='auto_save'
        ).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Auto-save draft deleted'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting draft: {str(e)}'
        }, status=400)

@login_required
@require_GET
def list_drafts(request):
    try:
        drafts = FormDraft.objects.filter(
            user=request.user,
            draft_type='manual'
        ).order_by('-updated_at')
        
        drafts_list = []
        for draft in drafts:
            drafts_list.append({
                'id': draft.id,
                'draft_name': draft.draft_name,
                'form_name': draft.form_name,
                'acronym': draft.acronym,
                'version': draft.version,
                'created_at': draft.created_at.isoformat(),
                'updated_at': draft.updated_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'drafts': drafts_list
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error listing drafts: {str(e)}'
        }, status=400)

@login_required
@require_GET
def load_draft(request, draft_id):
    try:
        draft = get_object_or_404(FormDraft, id=draft_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'draft': {
                'id': draft.id,
                'draft_name': draft.draft_name,
                'form_name': draft.form_name,
                'acronym': draft.acronym,
                'version': draft.version,
                'is_web': draft.is_web,
                'is_app': draft.is_app,
                'have_qc': draft.have_qc,
                'have_validation': draft.have_validation,
                'form_schema': draft.form_schema
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error loading draft: {str(e)}'
        }, status=400)

@login_required
@require_POST
def delete_draft(request, draft_id):
    try:
        draft = get_object_or_404(FormDraft, id=draft_id, user=request.user)
        draft.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Draft deleted successfully'
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error deleting draft: {str(e)}'
        }, status=400)

@login_required
@permission_required('subunits.manage_subunit', raise_exception=True)
@require_POST
def submit_form_schema(request, project_id, subunit_id=None):
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Parse the form data
        form_name = request.POST.get('form_name')
        acronym = request.POST.get('acronym')
        version = request.POST.get('version', '1')
        json_schema = request.POST.get('json_schema')
        
        # Parse JSON schema
        if json_schema:
            schema_data = json.loads(json_schema)
        else:
            raise ValueError("JSON schema is required")
        
        # Get settings from form
        is_web = request.POST.get('is_web') == '1'
        is_app = request.POST.get('is_app') == '1'
        have_qc = request.POST.get('have_qc') == '1'
        have_validation = request.POST.get('have_validation') == '1'
        
        if subunit_id:
            # Update existing subunit
            subunit = get_object_or_404(Subunit, id=subunit_id, project=project)
            subunit.name = form_name
            subunit.acronym = acronym
            subunit.version = version
            subunit.is_web = is_web
            subunit.is_app = is_app
            subunit.have_qc = have_qc
            subunit.have_validation = have_validation
            subunit.qnr_schema = schema_data
            subunit.updated_by = request.user
            subunit.save()
            
            messages.success(request, f'Subunit "{form_name}" updated successfully!')
        else:
            # Create new subunit
            subunit = Subunit.objects.create(
                project=project,
                name=form_name,
                acronym=acronym,
                version=version,
                is_web=is_web,
                is_app=is_app,
                have_qc=have_qc,
                have_validation=have_validation,
                qnr_schema=schema_data,
                created_by=request.user,
                updated_by=request.user
            )
            
            messages.success(request, f'Subunit "{form_name}" created successfully!')
        
        # Delete auto-save draft
        FormDraft.objects.filter(
            user=request.user,
            draft_type='auto_save'
        ).delete()
        
        return redirect('subunits:list', project_id=project.id)
    
    except Exception as e:
        messages.error(request, f'Error saving form: {str(e)}')
        return redirect('form_builder:builder', project_id=project_id)