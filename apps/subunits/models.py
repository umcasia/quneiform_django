# apps/subunits/models.py
from django.db import models
from django.conf import settings
from apps.projects.models import Project
from django.utils import timezone

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

    def __str__(self):
        return f"{self.name} ({self.acronym})"



# =====================================================
# SubunitTableMapping Model
# (Laravel: SubunitTableMapping)
# =====================================================
class SubunitTableMapping(models.Model):
    """
    Maps questionnaire sections to dynamically created tables
    """

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