from django.urls import path
from . import views


urlpatterns = [
    path('by-state/',  views.get_districts_by_state, name='district-by-state'),
    path('', views.district_list, name='district-list'),
    path('create/', views.district_create, name='district-create'),
    path('edit/<int:pk>/', views.district_edit, name='district-edit'),
    path('delete/<int:pk>/', views.district_delete, name='district-delete'),
]
