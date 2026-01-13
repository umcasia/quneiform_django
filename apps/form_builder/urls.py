# apps/form_builder/urls.py
from django.urls import path
from . import views

app_name = 'form_builder'

urlpatterns = [
    # Main form builder
    path('project/<int:project_id>/builder/', views.form_builder, name='builder'),
    path('project/<int:project_id>/builder/subunit/<int:subunit_id>/', views.form_builder, name='builder_edit'),
    
    # Draft management
    path('save-draft/', views.save_draft, name='save_draft'),
    path('auto-save-draft/', views.auto_save_draft, name='auto_save_draft'),
    path('get-auto-save-draft/', views.get_auto_save_draft, name='get_auto_save_draft'),
    path('delete-auto-save-draft/', views.delete_auto_save_draft, name='delete_auto_save_draft'),
    path('list-drafts/', views.list_drafts, name='list_drafts'),
    path('load-draft/<int:draft_id>/', views.load_draft, name='load_draft'),
    path('delete-draft/<int:draft_id>/', views.delete_draft, name='delete_draft'),
    
    # Form submission
    path('project/<int:project_id>/submit/', views.submit_form_schema, name='submit'),
    path('project/<int:project_id>/submit/subunit/<int:subunit_id>/', views.submit_form_schema, name='submit_edit'),
]