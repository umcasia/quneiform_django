from django.urls import path
from .views import Accounts

# urlpatterns = [
#     path("login/", LoginView.as_view(), name="login"),
#     path("register/", RegisterView.as_view(), name="register"),
#     path("logout/", LogoutView.as_view(), name="logout"),
#     path("password-reset/", PasswordResetView.as_view(), name="password_reset"),
# ]
urlpatterns = [
    # Login (GET shows form, POST processes form)
    path('login/', Accounts.as_view(), {'operation': 'login'}, name='login'),
    
    # Register (GET shows form, POST processes form)
    path('register/', Accounts.as_view(), {'operation': 'register'}, name='register'),
    
    # Logout (only GET needed)
    path('logout/', Accounts.as_view(), {'operation': 'logout'}, name='logout'),
    
    # Password Reset (GET shows form, POST processes form)
    path('password-reset/', Accounts.as_view(), {'operation': 'password_reset'}, name='password_reset'),
]