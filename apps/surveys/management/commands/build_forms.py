# management/commands/build_forms.py
from django.core.management.base import BaseCommand
from apps.subunits.models import Subunit
from apps.subunits.services.form_builder_service import FormBuilderService


class Command(BaseCommand):
    help = 'Build form structures from JSON schema for all subunits'
    
    def handle(self, *args, **options):
        subunits = Subunit.objects.filter(is_active=True)
        
        for subunit in subunits:
            self.stdout.write(f'Building form for {subunit.name}...')
            
            try:
                service = FormBuilderService(subunit)
                success = service.build_form_structure()
                
                if success:
                    self.stdout.write(self.style.SUCCESS(f'✓ Form built for {subunit.name}'))
                else:
                    self.stdout.write(self.style.ERROR(f'✗ Failed to build form for {subunit.name}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error building form for {subunit.name}: {e}'))
        
        self.stdout.write(self.style.SUCCESS('Form building completed!'))