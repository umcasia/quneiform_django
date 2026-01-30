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
# USERS VIEW (SINGLE CLASS FOR ALL CRUD OPERATIONS)
# =====================================================
class Users(LoginRequiredMixin, AdminOnlyMixin, View):    

    list_template = "user_list.html"
    create_template = "user_form.html"
    edit_template = "user_form_edit.html"
    
    # =====================================================
    # LIST USERS
    # =====================================================
    def get(self, request, pk=None):
        if pk and "edit" in request.path:
            return self.edit(request, pk)
        elif pk and "delete" in request.path:
            return self.delete(request, pk)
        elif "create" in request.path:
            return self.create(request)
        else:
            return self.list(request)
    
    def list(self, request):
        user = request.user
        search = request.GET.get('search', '')
        role_filter = request.GET.get('role', '')
        status_filter = request.GET.get('status', '')
        
        users = User.objects.filter(is_deleted=False).prefetch_related(
            'userhassurole_set__subunit',
            'userhassurole_set__role',
            'userhassudesignation_set__designation'
        )
        
        # Filter by user permissions
        if user.is_superuser:
            pass 
        elif getattr(user, 'is_organization_admin', False):
            users = users.filter(project_id=user.project_id)
        else:
            users = users.filter(id=user.id)  # Regular user only sees themselves
            
        # Search filter
        if search:
            users = users.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(mobile__icontains=search)
            )
        
        users = users.order_by('-date_joined')
        
        context = {
            'users': users,
            'search': search,
            'role_filter': role_filter,
            'status_filter': status_filter,
        }
        
        return render(request, self.list_template, context)
    
    # =====================================================
    # CREATE USER (FORM DISPLAY)
    # =====================================================
    def create(self, request):
        user = request.user
        
        user_superiority = UserHasSuRole.objects.filter(
            user=user
        ).aggregate(
            max_superiority=Max('role__superiority')
        )['max_superiority'] or 0
        
        if user.is_superuser:
            subunits = Subunit.objects.all()
        elif user.is_organization_admin:
            subunits = Subunit.objects.filter(project_id=user.project_id)
        else:
            subunit_ids = UserHasSuRole.objects.filter(user=user).values_list('subunit_id', flat=True)
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
            user_state_count = UserHasSuState.objects.filter(user=user).count()
            user_district_count = UserHasSuDistrict.objects.filter(user=user).count()
            user_city_count = UserHasSuCity.objects.filter(user=user).count()
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
        
        return render(request, self.create_template, context)
    
    # =====================================================
    # EDIT USER (FORM DISPLAY)
    # =====================================================
    def edit(self, request, pk):
        user_to_edit = get_object_or_404(User, pk=pk)
        current_user = request.user
        
        if not current_user.is_superuser and current_user.project_id != user_to_edit.project_id:
            raise PermissionDenied("You do not have permission to edit this user")
        
        user_roles = UserHasSuRole.objects.filter(user=user_to_edit).select_related('subunit', 'role')
        
        user_states = UserHasSuState.objects.filter(user=user_to_edit).values_list('state_id', flat=True).distinct()
        user_districts = UserHasSuDistrict.objects.filter(user=user_to_edit).values_list('district_id', flat=True).distinct()
        user_cities = UserHasSuCity.objects.filter(user=user_to_edit).values_list('city_id', flat=True).distinct()
        
        user_designation = UserHasSuDesignation.objects.filter(user=user_to_edit).first()
        
        current_user_superiority = UserHasSuRole.objects.filter(
            user=current_user
        ).aggregate(
            max_superiority=Max('role__superiority')
        )['max_superiority'] or 0
        
        if current_user.is_superuser:
            if getattr(user_to_edit, 'is_organization_admin', False):
                subunits = Subunit.objects.filter(project_id=user_to_edit.project_id)
            else:
                subunits = Subunit.objects.all()
        elif current_user.is_organization_admin:
            if user_to_edit.project_id == current_user.project_id:
                subunits = Subunit.objects.filter(project_id=current_user.project_id)
            else:
                raise PermissionDenied("You cannot edit users from another organization")
        else:
            subunit_ids = UserHasSuRole.objects.filter(user=current_user).values_list('subunit_id', flat=True)
            subunits = Subunit.objects.filter(id__in=subunit_ids)
        
        # Prepare subunit data with available roles and pre-selected role
        subunits_with_roles = []
        for subunit in subunits:
            roles = SuRole.objects.filter(
                subunit=subunit,
                superiority__gte=current_user_superiority
            ).values('id', 'name', 'superiority')
            
            current_role = None
            for user_role in user_roles:
                if user_role.subunit_id == subunit.id:
                    current_role = user_role.role_id
                    break
            
            subunits_with_roles.append({
                'id': subunit.id,
                'name': subunit.name,
                'acronym': subunit.acronym,
                'roles': list(roles),
                'current_role': current_role
            })
        
        states = State.objects.order_by('name').all()
        
        if not (current_user.is_superuser or current_user.is_organization_admin):
            user_state_count = UserHasSuState.objects.filter(user=current_user).count()
            user_district_count = UserHasSuDistrict.objects.filter(user=current_user).count()
            user_city_count = UserHasSuCity.objects.filter(user=current_user).count()
        else:
            user_state_count = 0
            user_district_count = 0
            user_city_count = 0
        
        context = {
            'edit_user': user_to_edit,
            'user_roles': list(user_roles),
            'user_states': list(user_states),
            'user_districts': list(user_districts),
            'user_cities': list(user_cities),
            'user_designation': user_designation.designation_id if user_designation else None,
            'subunits_with_roles': subunits_with_roles,
            'states': states,
            'designations': Designation.objects.filter(is_active=True).order_by('name'),
            'main_user_state_count': user_state_count,
            'main_user_district_count': user_district_count,
            'main_user_city_count': user_city_count,
            'superiority': current_user_superiority
        }
        
        return render(request, self.edit_template, context)
    
    # =====================================================
    # SAVE USER (CREATE/UPDATE)
    # =====================================================
    def post(self, request, pk=None):
        if pk:
            return self.update(request, pk)
        else:
            return self.store(request)
    
    def store(self, request):
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
                    self._assign_subunit_permissions(user, subunit_id, subunit_data, data)
                
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
    
    def update(self, request, pk):
        try:
            data = json.loads(request.body)
            
            user_to_edit = get_object_or_404(User, pk=pk)
            current_user = request.user
            
            if not current_user.is_superuser and current_user.project_id != user_to_edit.project_id:
                raise PermissionDenied("You do not have permission to edit this user")
            
            errors = self._validate_user_data(data, user_to_edit, is_update=True)
            if errors:
                return JsonResponse({'errors': errors}, status=422)
            
            with transaction.atomic():
                self._update_user(user_to_edit, data, current_user)
                
                UserHasSuRole.objects.filter(user=user_to_edit).delete()
                UserHasSuState.objects.filter(user=user_to_edit).delete()
                UserHasSuDistrict.objects.filter(user=user_to_edit).delete()
                UserHasSuCity.objects.filter(user=user_to_edit).delete()
                
                for subunit_id_str, subunit_data in data.get('subunit', {}).items():
                    try:
                        subunit_id = int(subunit_id_str)
                        self._assign_subunit_permissions(user_to_edit, subunit_id, subunit_data, data)
                    except (ValueError, Exception) as e:
                        print(f"Error assigning permissions for subunit {subunit_id_str}: {e}")
                        continue
                
                if data.get('designation_id'):
                    UserHasSuDesignation.objects.filter(user=user_to_edit).delete()
                    UserHasSuDesignation.objects.create(
                        user=user_to_edit,
                        designation_id=data.get('designation_id')
                    )
            
            return JsonResponse({
                'status': 200,
                'title': 'User updated successfully',
                'description': f"User with username {user_to_edit.username} updated successfully",
            }, status=200)
            
        except Exception as e:
            return JsonResponse({
                'error': 'An error occurred while updating the user',
                'message': str(e)
            }, status=500)
    
    # =====================================================
    # DELETE USER
    # =====================================================
    def delete(self, request, pk):
        user_obj = get_object_or_404(User, pk=pk)
        
        if not request.user.is_superuser and request.user.project_id != user_obj.project_id:
            raise PermissionDenied("You cannot delete this user")
        
        user_obj.is_deleted = True
        user_obj.save()
        
        messages.success(request, "User deleted successfully")
        return redirect("user_list")
    
    # =====================================================
    # PRIVATE HELPER METHODS
    # =====================================================
    def _validate_user_data(self, data, auth_user, is_update=False):
        errors = {}
        
        user_instance = None
        if is_update and hasattr(auth_user, 'pk'):
            user_instance = auth_user
        
        required_fields = ['name', 'username', 'email', 'mobile', 'designation_id']
        for field in required_fields:
            if not data.get(field):
                field_name = field.replace('_', ' ').title()
                errors[field] = [f'{field_name} is required']
        
        exclude_pk = user_instance.pk if user_instance else None
        
        if data.get('username'):
            qs = User.objects.filter(username=data['username'])
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                errors['username'] = ['Username already exists']
        
        if data.get('email'):
            qs = User.objects.filter(email=data['email'])
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                errors['email'] = ['Email already exists']
        
        if data.get('mobile'):
            qs = User.objects.filter(mobile=data['mobile'])
            if exclude_pk:
                qs = qs.exclude(pk=exclude_pk)
            if qs.exists():
                errors['mobile'] = ['Mobile number already exists']
        
        if not is_update and not data.get('password'):
            errors['password'] = ['Password is required']
        elif data.get('password') and len(data['password']) < 8:
            errors['password'] = ['Password must be at least 8 characters long']
        
        roles_selected = False
        for subunit_data in data.get('subunit', {}).values():
            if subunit_data.get('roles'):
                roles_selected = True
                break
        
        if not roles_selected:
            errors['roles'] = ['At least one role must be selected']
        
        if not data.get('states'):
            errors['states'] = ['At least one state must be selected']
        
        return errors
    
    def _create_user(self, data, auth_user):
        is_superadmin = data.get('superadmin') == 'true'
        if is_superadmin and not auth_user.is_superuser:
            raise PermissionDenied("Only superusers can create superadmin users")
        
        name_parts = data.get('name', '').split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=first_name,
            last_name=last_name,
            mobile=data['mobile'],
            is_superuser=is_superadmin,
            is_staff=is_superadmin,
            designation_id=data.get('designation_id'),
            project_id=auth_user.project_id if hasattr(auth_user, 'project_id') else None,
        )
        
        return user
    
    def _update_user(self, user, data, auth_user):
        is_superadmin = data.get('superadmin') == 'true'
        if is_superadmin and not auth_user.is_superuser:
            raise PermissionDenied("Only superusers can create superadmin users")
        
        name_parts = data.get('name', '').split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''
        
        user.username = data['username']
        user.email = data['email']
        user.mobile = data['mobile']
        user.first_name = first_name
        user.last_name = last_name
        user.is_superuser = is_superadmin
        user.is_staff = is_superadmin
        user.designation_id = data.get('designation_id')
        
        if data.get('password'):
            user.set_password(data['password'])
        
        user.save()
        return user
    
    def _assign_subunit_permissions(self, user, subunit_id, subunit_data, form_data):
        role_id = subunit_data.get('roles')
        
        if not role_id:
            return
        
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
# LOCATION CASCADE VIEW (SEPARATE API VIEW)
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