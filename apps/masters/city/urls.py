from django.urls import path
from . import views

urlpatterns = [
    path('ajax/', views.cities_by_district),
    path('', views.city_list, name='city-list'),
    path('create/', views.city_create, name='city-create'),
    path('edit/<int:pk>/', views.city_edit, name='city-edit'),
    path('delete/<int:pk>/', views.city_delete, name='city-delete'),
]
