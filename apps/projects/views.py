from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from apps.subunits.models import (UserHasSuDesignation)
import string
import random

from .models import Project

User = get_user_model()
class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.is_staff


class ApprovePermissionMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.has_perm("projects.approve_project")
def generate_unique_acronym():
    while True:
        acronym = ''.join(random.choices(string.ascii_uppercase, k=3))
        if not Project.objects.filter(acronym=acronym).exists():
            return acronym

class ProjectListView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "projects_list.html"

    def get(self, request):
        status_filter = request.GET.get("status", "")
        search_query = request.GET.get("search", "")

        projects = Project.objects.all()

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

        projects = projects.order_by("-created_at")

        context = {
            "projects": projects,
            "status_filter": status_filter,
            "search_query": search_query,
            "pending_count": Project.objects.filter(status="pending").count(),
            "approved_count": Project.objects.filter(status="approved").count(),
            "rejected_count": Project.objects.filter(status="rejected").count(),
            "total_count": Project.objects.count(),
        }

        return render(request, self.template_name, context)

class ApproveProjectView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    ApprovePermissionMixin,
    View
):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user

        try:
            with transaction.atomic():

                acronym = generate_unique_acronym()

                password = "welcome"
                if not settings.DEBUG:
                    password = User.objects.make_random_password()

                org_user, created = User.objects.get_or_create(
                    username=project.email,
                    defaults={
                        "email": project.email,
                        "first_name": project.contact_person or project.name,
                        "is_organization_admin": True,
                        "is_active": True,
                        "mobile": project.mobile,
                        "project_id": project.id,
                        "designation_id": project.designation_id,
                    }
                )

                if created:
                    org_user.set_password(password)
                    org_user.save()

                project.acronym = acronym
                project.status = "approved"
                project.is_active = True
                project.approved_by = user.id
                project.approved_at = timezone.now()
                project.save()
                
                if project.designation_id:
                    UserHasSuDesignation.objects.create(
                        user=user,
                        designation_id=project.designation_id
                    )

            messages.success(
                request,
                "Project approved & organization admin user created successfully"
            )

        except Exception as e:
            messages.error(request, str(e))

        return redirect("project_list")

class RejectProjectView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    ApprovePermissionMixin,
    View
):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user

        project.status = "rejected"
        project.is_active = False
        project.approved_by = user.id
        project.approved_at = timezone.now()
        project.save()

        messages.success(request, "Project rejected successfully")
        return redirect("project_list")

class RejectProjectView(
    LoginRequiredMixin,
    AdminRequiredMixin,
    ApprovePermissionMixin,
    View
):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        user = request.user

        project.status = "rejected"
        project.is_active = False
        project.approved_by = user.id
        project.approved_at = timezone.now()
        project.save()

        messages.success(request, "Project rejected successfully")
        return redirect("project_list")

class ProjectDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = "project_detail.html"

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        return render(request, self.template_name, {
            "project": project
        })
