import string
import random
from django.db import models
from apps.masters.states.models import State
from apps.masters.districts.models import District
from apps.masters.city.models import City
from apps.masters.designations.models import Designation

def generate_acronym():
    while True:
        acronym = ''.join(random.choices(string.ascii_uppercase, k=3))
        if not Project.objects.filter(acronym=acronym).exists():
            return acronym

class Project(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    name = models.CharField(max_length=255)
    project_name = models.CharField(max_length=255)

    acronym = models.CharField(
        max_length=10,
        unique=True,
        editable=False,
        default=generate_acronym
    )

    email = models.EmailField()
    contact_person = models.CharField(max_length=255)
    mobile = models.CharField(max_length=15)

    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)

    address = models.TextField(blank=True, null=True)
    gst_no = models.CharField(max_length=20, blank=True, null=True)
    logo = models.ImageField(upload_to='projects/logos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_active = models.BooleanField(default=False)
    approved_by = models.BigIntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'projects'

    def __str__(self):
        return f"{self.project_name} ({self.acronym})"
    
    @property
    def status_badge(self):
        badges = {
            'pending': 'warning',
            'approved': 'success',
            'rejected': 'danger'
        }
        return badges.get(self.status, 'secondary')
