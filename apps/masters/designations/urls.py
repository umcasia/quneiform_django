from django.urls import path
from . import views

urlpatterns = [
    path('', views.designation_list, name='designation-list'),
    path('create/', views.designation_create, name='designation-create'),
    path('edit/<int:pk>/', views.designation_edit, name='designation-edit'),
    path('delete/<int:pk>/', views.designation_delete, name='designation-delete'),
]
