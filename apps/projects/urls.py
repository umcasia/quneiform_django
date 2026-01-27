from django.urls import path
from .views import (
    ProjectListView,
    ApproveProjectView,
    RejectProjectView,
    ProjectDetailView,
)

urlpatterns = [
    path("", ProjectListView.as_view(), name="project_list"),
    path("<int:pk>/approve/", ApproveProjectView.as_view(), name="approve_project"),
    path("<int:pk>/reject/", RejectProjectView.as_view(), name="reject_project"),
    path("<int:pk>/", ProjectDetailView.as_view(), name="project_detail"),
]
