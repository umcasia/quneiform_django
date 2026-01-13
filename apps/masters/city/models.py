from django.db import models
from django.conf import settings
from django.db import models
from apps.masters.states.models import State
from apps.masters.districts.models import District
# from django.conf import settings

class City(models.Model):
    city_id = models.AutoField(primary_key=True)
    district = models.ForeignKey(District, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name="city_created"
    # )
    # updated_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name="city_updated"
    # )

    class Meta:
        db_table = 'masters_city'
        managed = True

    def __str__(self):
        return self.name

