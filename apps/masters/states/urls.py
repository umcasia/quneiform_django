from django.urls import path
from . import views

urlpatterns = [
    path('', views.state_list, name='state-list'),
    # path('export/', views.state_export, name='state-export'),
    path('create/', views.state_create, name='state-create'),
    path('edit/<int:pk>/', views.state_edit, name='state-edit'),
    path('delete/<int:pk>/', views.state_delete, name='state-delete'),
]
