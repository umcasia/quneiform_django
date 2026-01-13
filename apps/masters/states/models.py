from django.db import models

class State(models.Model):
    state_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, unique=True)
    short_name = models.CharField(max_length=10, unique=True, blank=True, null=True)  # ✅ ADD THIS
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'masters_state'
        managed = True

    def __str__(self):
        return self.name
