
from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.project_list, name="project_list"),
    path("<int:pk>/approve/", views.approve_project, name="project_approve"),
    path("<int:pk>/reject/", views.reject_project, name="project_reject"),
    path("<int:pk>/", views.project_detail, name="project_detail"),

]
