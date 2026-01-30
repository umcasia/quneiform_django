from django.db import models
from apps.masters.states.models import State
# from django.conf import settings

class District(models.Model):
    district_id = models.AutoField(primary_key=True)
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # created_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name="districts_created"
    # )
    # updated_by = models.ForeignKey(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     related_name="districts_updated"
    # )

    class Meta:
        db_table = 'masters_district'
        managed = True
        unique_together = ('name', 'state')
        ordering = ['name']

    def __str__(self):
        return self.name
