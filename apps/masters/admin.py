from django.contrib import admin
from apps.masters.states.models import State
from apps.masters.districts.models import District
from apps.masters.city.models import City

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ('state_id', 'name', 'created_at', 'updated_at')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('district_id', 'name', 'state', 'created_at')
    list_filter = ('state',)

@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('city_id', 'name', 'district', 'created_at')
    list_filter = ('district',)