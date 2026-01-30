from django.urls import path
from .views import Cities

urlpatterns = [
    path("by-district/", Cities.get_cities_by_district),
    path('', Cities.city_list, name='city-list'),
    path('create/', Cities.city_create, name='city-create'),
    path('edit/<int:pk>/', Cities.city_edit, name='city-edit'),
    path('delete/<int:pk>/', Cities.city_delete, name='city-delete'),
]
