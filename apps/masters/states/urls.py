from django.urls import path
from .views import States

urlpatterns = [
    path('', States.state_list, name='state-list'),
    # path('export/', views.state_export, name='state-export'),
    path('create/', States.state_create, name='state-create'),
    path('edit/<int:pk>/', States.state_edit, name='state-edit'),
    path('delete/<int:pk>/', States.state_delete, name='state-delete'),
]
