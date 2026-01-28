# urls.py
from django.urls import path
from .views import UserCreateView, UserListView, LocationCascadeView

urlpatterns = [
    path('', UserListView.as_view(), name='user_list'),
    path('create/', UserCreateView.as_view(), name='user_create'),
    path('create/<int:pk>/', UserCreateView.as_view(), name='user_edit'),
    path('delete/<int:pk>/', UserCreateView.as_view(), name='user_delete'),
    
    path('location/<str:location_type>/', LocationCascadeView.as_view(), name='location_cascade'),
    path('location/<str:location_type>/<int:parent_id>/', LocationCascadeView.as_view(), name='location_cascade_by_parent'),
]