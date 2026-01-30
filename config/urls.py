from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('apps.dashboard.urls')),
    
    path('accounts/', include('apps.accounts.urls')),
    path('projects/', include('apps.projects.urls')),
    path('projects/', include('apps.subunits.urls')),
    # path('subunits/', include('apps.subunits.urls')),
    # path('form-builder/', include('apps.form_builder.urls')),
    path("users/", include("apps.users.urls")),
    # Masters – portal
    path('masters/states/', include('apps.masters.states.urls')),
    path('masters/districts/', include('apps.masters.districts.urls')),
    path('masters/city/', include('apps.masters.city.urls')),
    path('masters/designations/', include('apps.masters.designations.urls')),

    path('survey/', include('apps.surveys.urls')),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
