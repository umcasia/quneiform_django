from django.urls import path
from . import views

urlpatterns = [
    path(
        'projects/<int:project_id>/subunits/',
        views.subunit_list,
        name='subunit_list'
    ),
    path(
        'projects/<int:project_id>/subunits/create/',
        views.subunit_create,
        name='subunit_create'
    ),
    # path(
    #     'subunits/<int:pk>/edit/',
    #     views.subunit_edit,
    #     name='subunit_edit'
    # ),
    # path(
    #     'subunits/<int:pk>/delete/',
    #     views.subunit_delete,
    #     name='subunit_delete'
    # ),
]
