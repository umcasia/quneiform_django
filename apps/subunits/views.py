from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
import json
from apps.projects.models import Project
from apps.subunits.models import Subunit
from apps.subunits.services.schema_base_service import SchemaBaseService
from apps.subunits.services.qnr_schema_validate_service import QnrSchemaValidateService
from apps.subunits.services.qnr_schema_register_service import QnrSchemaRegisterService
# from apps.subunits.services.subunit_service import SubunitService

@login_required
def subunit_list(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    if not (request.user.is_organization_admin or request.user.has_perm('subunits.manage_subunit')):
        messages.error(request, "Unauthorized")
        return redirect('project_list')

    subunits = project.subunits.all()

    return render(request, 'subunit_list.html', {
        'project': project,
        'subunits': subunits
    })

@login_required
def subunit_create(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    user = request.user

    if request.method == "POST":
        raw_schema = request.POST.get("json_schema")

        try:
            decoded_schema = SchemaBaseService.str_json_to_dict(raw_schema)

            # PHASE 1: ORM only
            with transaction.atomic():
                subunit = Subunit.objects.create(
                    project=project,
                    name=decoded_schema.get("form_name", "Auto Subunit"),
                    acronym=decoded_schema.get("acronym", "AUTO"),
                    version=1,
                    active=True,
                    is_web=True,
                    is_app=bool(request.POST.get("is_app")),
                    have_qc=bool(request.POST.get("have_qc")),
                    have_validation=bool(request.POST.get("have_validation")),
                    qnr_schema=decoded_schema,
                    view_home_map={},          # ✅ REQUIRED
                    filter_home_map={},        # ✅ REQUIRED
                    created_by=user,
                )

                QnrSchemaValidateService(decoded_schema).validate_form_schema()

            # PHASE 2: DDL (NO atomic)
            QnrSchemaRegisterService(
                user_id=user.id,
                subunit_id=subunit.id,
                project_acronym=project.acronym,
                subunit_acronym=subunit.acronym,
                have_qc=subunit.have_qc,
                have_validation=subunit.have_validation,
            ).register_schema(decoded_schema)

        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect(request.path)

        messages.success(request, "Subunit created successfully")
        return redirect("subunit_list", project_id=project.id)

    return render(request, "subunit_form.html", {"project": project})
def register_schema(self, schema):
    try:
        self._process_sections(schema["data"])
        self._update_subunit_maps()
        self._create_sysgen_tables()
    except Exception:
        self._rollback()
        raise

# @login_required
# def subunit_create(request, project_id):
#     project = get_object_or_404(Project, id=project_id)

#     if request.method == 'POST':
#         Subunit.objects.create(
#             project=project,
#             is_web=bool(request.POST.get('is_web')),
#             is_app=bool(request.POST.get('is_app')),
#             have_qc=bool(request.POST.get('have_qc')),
#             have_validation=bool(request.POST.get('have_validation')),
#             view_home_map=bool(request.POST.get('view_home_map')),
#             version=request.POST['version'],
#             name=request.POST['form_name'],
#             acronym=request.POST['acronym'],
#             qnr_schema=request.POST['json_schema'],
#             created_by=request.user,
#             updated_by=request.user
#         )
#         messages.success(request, "Subunit created")
#         return redirect('subunit_list', project_id=project.id)

#     return render(request, 'subunit_form.html', {'project': project})
