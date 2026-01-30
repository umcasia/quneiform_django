from django.urls import path
from .views import Districts


urlpatterns = [
    path('by-state/',  Districts.get_districts_by_state, name='district-by-state'),
    path('', Districts.district_list, name='district-list'),
    path('create/', Districts.district_create, name='district-create'),
    path('edit/<int:pk>/', Districts.district_edit, name='district-edit'),
    path('delete/<int:pk>/', Districts.district_delete, name='district-delete'),
]
