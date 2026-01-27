# apps/subunits/models.py
from django.db import models
from django.conf import settings
from apps.projects.models import Project
from django.utils import timezone
from apps.masters.states.models import State
from apps.masters.districts.models import District
from apps.masters.city.models import City
from apps.masters.designations.models import Designation
from django.contrib.auth import get_user_model

User = get_user_model()

class Subunit(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='subunits'
    )

    name = models.CharField(max_length=255)
    acronym = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    active = models.BooleanField(default=True)
    is_web = models.BooleanField(default=False)
    is_app = models.BooleanField(default=False)
    have_qc = models.BooleanField(default=False)
    have_validation = models.BooleanField(default=False)

    version = models.CharField(max_length=20, blank=True, null=True)

    qnr_schema = models.JSONField(blank=True, null=True)
    lang_schema = models.JSONField(blank=True, null=True)
    post_qc_validation_schema = models.JSONField(blank=True, null=True)

    view_home_map = models.JSONField(default=dict)
    filter_home_map = models.JSONField(default=dict)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subunit_created'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='subunit_updated'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subunits'
        permissions = [
            ('manage_subunit', 'Can manage subunits'),
        ]
        
        unique_together = ("project", "name")      # same project cannot have same name
        constraints = [
            models.UniqueConstraint(fields=["project", "acronym"], name="unique_project_acronym")
        ]

    def __str__(self):
        return f"{self.name} ({self.acronym})"


# =====================================================
# SubunitTableMapping Model
# (Laravel: SubunitTableMapping)
# =====================================================
class SubunitTableMapping(models.Model):
    subunit = models.ForeignKey(
        Subunit,
        on_delete=models.CASCADE,
        related_name="table_mappings"
    )

    section_name = models.CharField(max_length=255)
    section_acronym = models.CharField(max_length=50)

    table_name = models.CharField(max_length=255, unique=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_mappings",
        db_column="parent_subunit_table_mapping_id"
    )

    fields = models.JSONField(default=list)
    acronym_sequence = models.JSONField(default=list)

    # Soft delete (Laravel SoftDeletes)
    deleted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "subunit_table_mappings"
        ordering = ["id"]

    def __str__(self):
        return f"{self.section_name} → {self.table_name}"

    # ---------------------------------
    # Soft delete helpers
    # ---------------------------------
    def soft_delete(self):
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])
        
        
class Permission(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class SuRole(models.Model):
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    superiority = models.IntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )

    def __str__(self):
        return f"{self.name} ({self.subunit.acronym})"


class SuRoleHasPermission(models.Model):
    role = models.ForeignKey(SuRole, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:        
        unique_together = ("role", "permission")


class UserHasSuRole(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    role = models.ForeignKey(SuRole, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "subunit")

class UserHasSuState(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    state = models.ForeignKey(State, on_delete=models.CASCADE)

class UserHasSuDistrict(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    district = models.ForeignKey(District, on_delete=models.CASCADE)

class UserHasSuCity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subunit = models.ForeignKey(Subunit, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

class UserHasSuDesignation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    designation = models.ForeignKey(Designation, on_delete=models.CASCADE)
