from django.urls import path
from .views import Designations

urlpatterns = [
    path('', Designations.designation_list, name='designation-list'),
    path('create/', Designations.designation_create, name='designation-create'),
    path('edit/<int:pk>/', Designations.designation_edit, name='designation-edit'),
    path('delete/<int:pk>/', Designations.designation_delete, name='designation-delete'),
]
