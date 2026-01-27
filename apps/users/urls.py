from django.urls import path
from apps.users.views import UserView

urlpatterns = [
    path("", UserView.as_view(), name="user_list"),
    path("create/", UserView.as_view(), name="user_create"),
    path("<int:pk>/edit/", UserView.as_view(), name="user_edit"),
    path("<int:pk>/delete/", UserView.as_view(), name="user_delete"),
]
