# middleware/dynamic_table_middleware.py
from django.db import connection
from django.apps import apps


class DynamicTableMiddleware:
    """Middleware to handle dynamic table operations"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Add dynamic table models to request if needed
        if hasattr(request, 'dynamic_models'):
            return
        
        # Get subunit from URL or session
        subunit_id = view_kwargs.get('subunit_id')
        if not subunit_id:
            return
        
        try:
            from apps.subunits.models import Subunit
            subunit = Subunit.objects.get(id=subunit_id)
            
            # Load dynamic models for this subunit
            request.dynamic_models = self._load_dynamic_models(subunit)
            
        except Exception:
            request.dynamic_models = {}
    
    def _load_dynamic_models(self, subunit):
        """Load dynamic models for a subunit"""
        models = {}
        
        # Get all table names for this subunit
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE %s
            """, [f"{subunit.project.acronym}_{subunit.acronym}_%"])
            
            tables = cursor.fetchall()
            
            for table in tables:
                table_name = table[0]
                try:
                    # Try to get the model from apps
                    model = apps.get_model('subunits.dynamic', table_name)
                    models[table_name] = model
                except LookupError:
                    # Model not registered, skip
                    continue
        
        return models