# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('form/<int:subunit_id>/', views.DynamicFormView.as_view(), name='dynamic_form'),
    path('form/<int:subunit_id>/<int:submission_id>/', views.DynamicFormView.as_view(), name='edit_submission'),
    path('submissions/<int:subunit_id>/', views.FormSubmissionListView.as_view(), name='form_submission_list'),
    path('submission/<int:submission_id>/', views.FormSubmissionDetailView.as_view(), name='form_submission_detail'),
    path('api/form-data/<int:subunit_id>/', views.FormDataAPIView.as_view(), name='form_data_api'),
]