from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Project
from django.db.models import Q
from django.conf import settings
from django.db import transaction
import string
import random

User = get_user_model()

def is_admin(user):
    return user.is_superuser or user.is_staff

def has_approve_permission(user):
    if user.is_superuser:
        return True
    return user.has_perm("projects.approve_project")

def generate_unique_acronym():
    while True:
        acronym = ''.join(random.choices(string.ascii_uppercase, k=3))
        if not Project.objects.filter(acronym=acronym).exists():
            return acronym
        
@login_required
@user_passes_test(is_admin)
def project_list(request):
    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Start with all projects
    projects = Project.objects.all()
    
    # Apply filters
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    if search_query:
        projects = projects.filter(
            Q(name__icontains=search_query) |
            Q(project_name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(mobile__icontains=search_query)
        )
    
    # Order by creation date (newest first)
    projects = projects.order_by('-created_at')
    
    # Count by status
    pending_count = Project.objects.filter(status='pending').count()
    approved_count = Project.objects.filter(status='approved').count()
    rejected_count = Project.objects.filter(status='rejected').count()
    total_count = Project.objects.count()
    
    context = {
        'projects': projects,
        'status_filter': status_filter,
        'search_query': search_query,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': total_count,
    }
    return render(request, 'projects_list.html', context)
@login_required
@user_passes_test(is_admin)
def approve_project(request, pk):
    if request.method != "POST":
        return redirect("project_list")

    user = request.user

    if not has_approve_permission(user):
        messages.error(request, "Unauthorized")
        return redirect("project_list")

    project = get_object_or_404(Project, pk=pk)

    try:
        with transaction.atomic():

            # Generate acronym
            acronym = generate_unique_acronym()

            # Password logic
            password = "welcome"
            if not settings.DEBUG:
                password = User.objects.make_random_password()

            # Create organization admin user
            org_user, created = User.objects.get_or_create(
                username=project.email,
                defaults={
                    "email": project.email,
                    "first_name": project.contact_person or project.name,
                    "is_organization_admin": True,
                    "is_active": True,
                    "mobile": project.mobile,
                    'project_id':project.id,
                }
            )

            if created:
                org_user.set_password(password)
                org_user.save()

            # Update project
            project.acronym = acronym
            project.status = "approved"
            project.is_active = True
            project.approved_by = user.id 
            project.approved_at = timezone.now()
            project.save()

            # (Optional) Email
            # send_mail(...)

        messages.success(request, "Project approved & admin user created")

    except Exception as e:
        messages.error(request, str(e))

    return redirect("project_list")


@login_required
@user_passes_test(is_admin)
def reject_project(request, pk):
    if request.method != "POST":
        return redirect("project_list")

    user = request.user

    if not has_approve_permission(user):
        messages.error(request, "Unauthorized")
        return redirect("project_list")

    project = get_object_or_404(Project, pk=pk)

    project.status = "rejected"
    project.is_active = False
    project.approved_by = user.id 
    project.approved_at = timezone.now()
    project.save()

    messages.success(request, "Project rejected successfully")
    return redirect("project_list")

@login_required
@user_passes_test(is_admin)
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    return render(request, 'project_detail.html', {'project': project})
def create_project_admin_user(project):
    User = get_user_model()

    if User.objects.filter(email=project.email).exists():
        return

    user = User.objects.create_user(
        username=project.email,
        email=project.email,
        password='welcome',
        first_name=project.contact_person,
        is_active=True,
        is_staff=True
    )

    user.must_change_password = True
    user.save()
