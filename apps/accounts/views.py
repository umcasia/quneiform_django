# views/account_views.py
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.contrib.auth import get_user_model
from django.http import JsonResponse
import json

from apps.projects.models import Project
from apps.masters.states.models import State
from apps.masters.designations.models import Designation

User = get_user_model()


# =====================================================
# ACCOUNTS VIEW (SINGLE CLASS FOR ALL ACCOUNT OPERATIONS)
# =====================================================
class Accounts(View):
    # Template names
    login_template = "login.html"
    register_template = "register.html"
    password_reset_template = "password_reset.html"
    
    # =====================================================
    # ROUTE HANDLER
    # =====================================================
    def get(self, request, operation=None, pk=None):
        if operation == 'logout':
            return self.logout(request)
        elif operation == 'password_reset':
            return self.password_reset(request)
        elif operation == 'register':
            return self.register(request)
        else:
            return self.login(request)
    
    def post(self, request, operation=None, pk=None):
        if operation == 'login':
            return self.process_login(request)
        elif operation == 'register':
            return self.process_register(request)
        elif operation == 'password_reset':
            return self.process_password_reset(request)
        else:
            return redirect('login')
    
    # =====================================================
    # LOGIN OPERATIONS
    # =====================================================
    def login(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.login_template)
    
    def process_login(self, request):
        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                username = data.get("username")
                password = data.get("password")
            except json.JSONDecodeError:
                return JsonResponse({
                    'error': 'Invalid JSON data',
                    'message': 'Please provide valid login credentials'
                }, status=400)
        else:
            username = request.POST.get("username")
            password = request.POST.get("password")
        
        if not username or not password:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Missing credentials',
                    'message': 'Username and password are required'
                }, status=400)
            else:
                messages.error(request, "Username and password are required")
                return render(request, self.login_template)
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'status': 200,
                        'title': 'Login successful',
                        'description': f'Welcome back, {user.get_full_name() or user.username}!',
                        'redirect_url': '/dashboard/'  # Change this to your actual dashboard URL
                    }, status=200)
                else:
                    return redirect("dashboard")
            else:
                if request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'Account inactive',
                        'message': 'Your account has been deactivated. Please contact support.'
                    }, status=403)
                else:
                    messages.error(request, "Your account has been deactivated. Please contact support.")
        else:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Authentication failed',
                    'message': 'Invalid username or password'
                }, status=401)
            else:
                messages.error(request, "Invalid username or password")
        
        return render(request, self.login_template)
    
    # =====================================================
    # REGISTER OPERATIONS
    # =====================================================
    def register(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        
        states = State.objects.filter(is_active=True).order_by("name")
        designations = Designation.objects.filter(is_active=True).order_by("name")
        
        return render(request, self.register_template, {
            "states": states,
            "designations": designations
        })
    
    def process_register(self, request):
        if request.user.is_authenticated:
            if request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Already logged in',
                    'message': 'You are already logged in. Please logout first to register a new account.'
                }, status=400)
            else:
                messages.warning(request, "You are already logged in. Please logout first to register a new account.")
                return redirect("dashboard")
        
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST.dict()
                if request.FILES.get('logo'):
                    data['logo'] = request.FILES.get('logo')
            
            errors = self._validate_registration_data(data)
            if errors:
                if request.content_type == 'application/json':
                    return JsonResponse({'errors': errors}, status=422)
                else:
                    for field, error_list in errors.items():
                        for error in error_list:
                            messages.error(request, f"{field.replace('_', ' ').title()}: {error}")
                    return redirect("register")
            
            with transaction.atomic():
                project = Project.objects.create(
                    name=data.get("org_name"),
                    email=data.get("email"),
                    contact_person=data.get("contact_person"),
                    designation_id=data.get("designation_id"),
                    mobile=data.get("mobile"),
                    state_id=data.get("state_id"),
                    district_id=data.get("district_id"),
                    city_id=data.get("city_id"),
                    address=data.get("address"),
                    gst_no=data.get("gst_no"),
                    logo=data.get("logo") if isinstance(data.get("logo"), object) else None,
                    is_active=False,
                )
            
            success_message = "Project registered successfully. Await admin approval."
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'status': 200,
                    'title': 'Registration successful',
                    'description': success_message,
                    'redirect_url': '/accounts/login/' 
                }, status=200)
            else:
                messages.success(request, success_message)
                return redirect("login")
            
        except Exception as e:
            error_message = f"Registration failed: {str(e)}"
            
            if request.content_type == 'application/json':
                return JsonResponse({
                    'error': 'Registration failed',
                    'message': error_message
                }, status=500)
            else:
                messages.error(request, error_message)
                return redirect("register")
    
    # =====================================================
    # LOGOUT OPERATION
    # =====================================================
    def logout(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "You have been logged out successfully.")
        else:
            messages.info(request, "You are already logged out.")
        
        return redirect("login")
    
    # =====================================================
    # PASSWORD RESET OPERATIONS
    # =====================================================
    def password_reset(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.password_reset_template)
    
    def process_password_reset(self, request):
        if request.content_type == 'application/json':
            return JsonResponse({
                'status': 200,
                'title': 'Password reset email sent',
                'description': 'If an account exists with the email provided, you will receive password reset instructions shortly.'
            }, status=200)
        else:
            messages.success(request, "If an account exists with the email provided, you will receive password reset instructions shortly.")
            return redirect("login")
    
    # =====================================================
    # PRIVATE HELPER METHODS
    # =====================================================
    def _validate_registration_data(self, data):
        errors = {}
        
        required_fields = [
            'org_name', 'email', 'contact_person', 'designation_id',
            'mobile', 'state_id'
        ]
        
        for field in required_fields:
            if not data.get(field):
                field_name = field.replace('_', ' ').title()
                errors[field] = [f'{field_name} is required']
        
        email = data.get('email')
        if email:
            if '@' not in email or '.' not in email:
                errors['email'] = ['Please enter a valid email address']
            
            if Project.objects.filter(email__iexact=email).exists():
                errors['email'] = ['This email is already registered']
        
        mobile = data.get('mobile')
        if mobile:
            if not mobile.isdigit() or len(mobile) < 10:
                errors['mobile'] = ['Please enter a valid 10-digit mobile number']
        
        gst_no = data.get('gst_no')
        if gst_no:
            if len(gst_no) != 15 or not gst_no.isalnum():
                errors['gst_no'] = ['Please enter a valid 15-character GST number']
        
        return errors