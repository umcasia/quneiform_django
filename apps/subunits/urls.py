from django.urls import path
from apps.subunits.views import SubunitView

urlpatterns = [
    path(
        "projects/<int:project_id>/subunits/",
        SubunitView.as_view(),
        name="subunit_list",
    ),
    path(
        "projects/<int:project_id>/subunits/create/",
        SubunitView.as_view(),
        name="subunit_create",
    ),
]
