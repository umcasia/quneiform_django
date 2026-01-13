from django.db import models

class Designation(models.Model):
    designation_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'masters_designation'

    def __str__(self):
        return self.name