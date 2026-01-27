from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction

from apps.projects.models import Project
from apps.subunits.models import Subunit
from apps.subunits.services.schema_base_service import SchemaBaseService
from apps.subunits.services.qnr_schema_validate_service import QnrSchemaValidateService
from apps.subunits.services.qnr_schema_register_service import QnrSchemaRegisterService
from apps.subunits.services.auto_role_creator_service import AutoRoleCreatorService

class SubunitPermissionMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return (
            user.is_organization_admin
            or user.has_perm("subunits.manage_subunit")
        )


class SubunitView(
    LoginRequiredMixin,
    SubunitPermissionMixin,
    View
):
    template_name = "subunit_list.html"
    form_template_name = "subunit_form.html"

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        # If ?create=1 → show create form
        if request.GET.get("create") == "1":
            return render(request, "subunit_form.html", {
                "project": project
            })

        # Otherwise → list view
        subunits = project.subunits.all()
        return render(request, self.template_name, {
            "project": project,
            "subunits": subunits,
        })


    def post(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        user = request.user

        raw_schema = request.POST.get("json_schema")
        if not raw_schema:
            messages.error(request, "JSON schema is required")
            return redirect(request.path)

        try:
            decoded_schema = SchemaBaseService.str_json_to_dict(raw_schema)
            # Extract values correctly
            name = decoded_schema.get("form_name", "Auto Subunit")
            acronym = decoded_schema.get("acronym", "AUTO")

            # Ensure string only (extra safety)
            name = str(name).strip()
            acronym = str(acronym).strip().upper()

            # 🔥 UNIQUE CHECK BEFORE DB TRANSACTION
            if Subunit.objects.filter(project=project, name=name).exists():
                messages.error(request, "Subunit name already exists")
                return redirect(request.path)

            if Subunit.objects.filter(project=project, acronym=acronym).exists():
                messages.error(request, "Subunit acronym already exists")
                return redirect(request.path)
        
            # ---------------------------------------------
            # PHASE 1: ORM + VALIDATION (ATOMIC)
            # ---------------------------------------------
            with transaction.atomic():
                subunit = Subunit.objects.create(
                    project=project,
                    name=name,
                    acronym=acronym,
                    version=decoded_schema.get("version", "1.0"),
                    active=True,
                    is_web=True,
                    is_app=bool(request.POST.get("is_app")),
                    have_qc=bool(request.POST.get("have_qc")),
                    have_validation=bool(request.POST.get("have_validation")),
                    qnr_schema=decoded_schema,
                    view_home_map={},
                    filter_home_map={},
                    created_by=user,
                )

                # Validate schema structure
                QnrSchemaValidateService(
                    decoded_schema
                ).validate_form_schema()

            # ---------------------------------------------
            # PHASE 2: DYNAMIC TABLE CREATION (NO atomic)
            # ---------------------------------------------
            QnrSchemaRegisterService(
                user_id=user.id,
                subunit_id=subunit.id,
                project_acronym=project.acronym,
                subunit_acronym=subunit.acronym,
                have_qc=subunit.have_qc,
                have_validation=subunit.have_validation,
            ).register_schema(decoded_schema)

            # After subunit created
            AutoRoleCreatorService.create_roles_for_subunit(subunit, user)

        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect(request.path)

        messages.success(request, "Subunit created successfully")
        return redirect("subunit_list", project_id=project.id)
