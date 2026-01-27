from django.urls import path
from apps.accounts.views import (
    LoginView,
    RegisterView,
    LogoutView,
    PasswordResetView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
]
