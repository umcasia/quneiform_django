# urls.py
from django.urls import path
from .views import Users, LocationCascadeView

urlpatterns = [
    path('', Users.as_view(), name='user_list'),
    path('create/', Users.as_view(), name='user_create'),
    path('edit/<int:pk>/', Users.as_view(), name='user_edit'),
    path('delete/<int:pk>/', Users.as_view(), name='user_delete'),
    
    path('location/<str:location_type>/', LocationCascadeView.as_view(), name='location_cascade'),
    path('location/<str:location_type>/<int:parent_id>/', LocationCascadeView.as_view(), name='location_cascade_by_parent'),
]