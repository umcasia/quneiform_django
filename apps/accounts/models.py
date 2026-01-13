from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    mobile = models.CharField(max_length=15, blank=True, null=True)
    is_organization_admin = models.BooleanField(default=False)

    project_id = models.IntegerField(blank=True, null=True)

    designation = models.CharField(max_length=255, blank=True, null=True)
    designation_id = models.IntegerField(blank=True, null=True)

    email_verified_at = models.DateTimeField(null=True, blank=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    remember_token = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
