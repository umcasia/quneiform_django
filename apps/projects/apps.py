from django.apps import AppConfig
from pathlib import Path

class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'

    def ready(self):
        from django.conf import settings
        project_templates = Path(__file__).resolve().parent / 'templates'
        if project_templates not in settings.TEMPLATES[0]['DIRS']:
            settings.TEMPLATES[0]['DIRS'].append(project_templates)
