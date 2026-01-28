# views/user_views.py
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.db import transaction
from django.db.models import Max, Q
from django.http import JsonResponse
from django.contrib import messages
from django.core.exceptions import PermissionDenied
import json

from apps.projects.models import Project
from apps.subunits.models import (
    Subunit, SuRole, UserHasSuRole,
    UserHasSuState, UserHasSuDistrict, UserHasSuCity,
    UserHasSuDesignation, SuRoleHasPermission
)
from apps.masters.states.models import State
from apps.masters.districts.models import District
from apps.masters.city.models import City
from apps.masters.designations.models import Designation

User = get_user_model()


# =====================================================
# PERMISSION MIXIN
# =====================================================
class AdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_superuser or getattr(user, 'is_organization_admin', False)


# =====================================================
# USER CREATE VIEW
# =====================================================
class UserCreateView(LoginRequiredMixin, AdminOnlyMixin, View):
    template_name = "user_form.html"
    
    def get(self, request):
        user = request.user
        
        user_superiority = UserHasSuRole.objects.filter(
            user=user
        ).aggregate(
            max_superiority=Max('role__superiority')
        )['max_superiority'] or 0
        
        if user.is_superuser:
            subunits = Subunit.objects.all()
        elif user.is_organization_admin:
            subunits = Subunit.objects.filter(
                project_id=user.project_id
            )
        else:
            subunit_ids = UserHasSuRole.objects.filter(
                user=user
            ).values_list('subunit_id', flat=True)
            subunits = Subunit.objects.filter(id__in=subunit_ids)
        
        subunits_with_roles = []
        for subunit in subunits:
            roles = SuRole.objects.filter(
                subunit=subunit,
                superiority__gte=user_superiority
            ).values('id', 'name', 'superiority')
            
            subunits_with_roles.append({
                'id': subunit.id,
                'name': subunit.name,
                'acronym': subunit.acronym,
                'roles': list(roles)
            })
        
        states = State.objects.order_by('name').all()
        
        if not (user.is_superuser or user.is_organization_admin):
            user_state_count = UserHasSuState.objects.filter(
                user=user
            ).count()
            user_district_count = UserHasSuDistrict.objects.filter(
                user=user
            ).count()
            user_city_count = UserHasSuCity.objects.filter(
                user=user
            ).count()
        else:
            user_state_count = 0
            user_district_count = 0
            user_city_count = 0
        
        context = {
            'user': user,
            'subunits_with_roles': subunits_with_roles,
            'states': states,
            'designations': Designation.objects.filter(is_active=True).order_by('name'),
            'main_user_state_count': user_state_count,
            'main_user_district_count': user_district_count,
            'main_user_city_count': user_city_count,
            'superiority': user_superiority
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        try:
    
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
                data['states'] = request.POST.getlist('states')
                data['districts'] = request.POST.getlist('districts')
                data['cities'] = request.POST.getlist('cities')
                data['roles'] = request.POST.getlist('roles')
                
                data['subunit'] = {}
                for key in request.POST.keys():
                    if key.startswith('subunit[') and key.endswith('][roles]'):
                        subunit_id = key.split('[')[1].split(']')[0]
                        role_id = request.POST[key]
                        data['subunit'][subunit_id] = {'roles': role_id}                        
            
            errors = self._validate_user_data(data, request.user)
            if errors:
                return JsonResponse({'errors': errors}, status=422)
            
            with transaction.atomic():
                user = self._create_user(data, request.user)
                
                for subunit_id, subunit_data in data.get('subunit', {}).items():
                    self._assign_subunit_permissions(
                        user, subunit_id, subunit_data, data
                    )
                
                if data.get('designation_id'):
                    UserHasSuDesignation.objects.create(
                        user=user,
                        designation_id=data.get('designation_id')
                    )
            
            return JsonResponse({
                'status': 200,
                'title': 'User created successfully',
                'description': f"User with username {data['username']} created successfully",
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while creating the user',
                'message': str(e)
            }, status=500)
    
    def _validate_user_data(self, data, auth_user):
        errors = {}
        
        if not data.get('name'):
            errors['name'] = ['Name is required']
        
        if not data.get('username'):
            errors['username'] = ['Username is required']
        elif User.objects.filter(username=data['username']).exists():
            errors['username'] = ['Username already exists']
        
        if not data.get('email'):
            errors['email'] = ['Email is required']
        elif User.objects.filter(email=data['email']).exists():
            errors['email'] = ['Email already exists']
        
        if not data.get('mobile'):
            errors['mobile'] = ['Mobile number is required']
        elif User.objects.filter(mobile=data['mobile']).exists():
            errors['mobile'] = ['Mobile number already exists']
        
        if not data.get('password'):
            errors['password'] = ['Password is required']
        else:
            password = data['password']
            if len(password) < 8:
                errors['password'] = ['Password must be at least 8 characters long']
        
        if not data.get('designation_id'):
            errors['designation_id'] = ['Designation is required']
        
        roles_selected = False
        for subunit_data in data.get('subunit', {}).values():
            if subunit_data.get('roles'):
                roles_selected = True
                break
        
        if not roles_selected:
            errors['roles'] = ['At least one role must be selected']
        
        if 'states' in data and not data['states']:
            errors['states'] = ['At least one state must be selected']
        
        return errors
    
    def _create_user(self, data, auth_user):
        is_superadmin = data.get('superadmin') == 'true'
        if is_superadmin and not auth_user.is_superuser:
            raise PermissionDenied("Only superusers can create superadmin users")
        
        name_parts = data.get('name', '').split(' ')
        first_name = name_parts[0] if name_parts else data.get('name', '')
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
            mobile=data['mobile'],
            is_superuser=is_superadmin,
            is_staff=is_superadmin or data.get('is_organization_admin', False),
            designation_id=data.get('designation_id', ''),
            project_id=auth_user.project_id if hasattr(auth_user, 'project_id') else None,
            # created_by=auth_user,
            # updated_by=auth_user
        )
        
        return user
    
    def _assign_subunit_permissions(self, user, subunit_id, subunit_data, form_data):
        role_id = subunit_data.get('roles')
        
        if not role_id:
            return
        
        subunit_id = int(subunit_id)
        UserHasSuRole.objects.create(
            user=user,
            subunit_id=subunit_id,
            role_id=role_id
        )
        
        if form_data.get('states'):
            for state_id in form_data['states']:
                UserHasSuState.objects.create(
                    user=user,
                    subunit_id=subunit_id,
                    state_id=state_id
                )
        
        if form_data.get('districts'):
            for district_id in form_data['districts']:
                UserHasSuDistrict.objects.create(
                    user=user,
                    subunit_id=subunit_id,
                    district_id=district_id
                )
        
        if form_data.get('cities'):
            for city_id in form_data['cities']:
                UserHasSuCity.objects.create(
                    user=user,
                    subunit_id=subunit_id,
                    city_id=city_id
                )


# =====================================================
# USER LIST VIEW
# =====================================================
class UserListView(LoginRequiredMixin, AdminOnlyMixin, View):
    template_name = "user_list.html"
    
    def get(self, request):
        user = request.user
        search = request.GET.get('search', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        
        users = User.objects.all().prefetch_related(
            'userhassurole_set__subunit',
            'userhassurole_set__role',
            'userhassudesignation_set__designation'
        )
        
        if user.is_superuser:
            pass
        
        elif getattr(user, 'is_organization_admin', False):
            users = users.filter(project_id=user.project_id)

        else:
            users = users.filter(id=user.id)
            
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(mobile__icontains=search)
            )
        
        if role_filter == 'admin':
            users = users.filter(is_superuser=True)
        elif role_filter == 'staff':
            users = users.filter(is_staff=True)
        
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)
        
        users = users.order_by('-date_joined')
        
        context = {
            'users': users,
            'search': search,
            'role_filter': role_filter,
            'status_filter': status_filter,
        }
        
        return render(request, self.template_name, context)


# =====================================================
# LOCATION CASCADE VIEW
# =====================================================
class LocationCascadeView(View):
    def get(self, request, location_type, parent_id=None):
        try:
            location_type = location_type.lower()
            data = []
            
            if location_type == 'states':
                states = State.objects.order_by('name')
                data = [{'id': s.state_id, 'name': s.name} for s in states]
            
            elif location_type == 'districts':
                state_ids = request.GET.getlist('state_ids[]', [])
                if state_ids:
                    districts = District.objects.filter(
                        state_id__in=state_ids
                    ).order_by('name')
                    data = [{'id': d.district_id, 'name': d.name} for d in districts]
            
            elif location_type == 'cities':
                district_ids = request.GET.getlist('district_ids[]', [])
                if district_ids:
                    cities = City.objects.filter(
                        district_id__in=district_ids
                    ).order_by('name')
                    data = [{'id': c.city_id, 'name': c.name} for c in cities]
            
            return JsonResponse(data, safe=False)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)