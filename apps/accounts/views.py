from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
from apps.projects.models import Project
from apps.masters.states.models import State

User = get_user_model()

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():

                Project.objects.create(
                    name=request.POST['org_name'],
                    email=request.POST['email'],
                    contact_person=request.POST['contact_person'],
                    designation=request.POST['designation'],
                    mobile=request.POST['mobile'],
                    state_id=request.POST.get('state_id'),
                    district_id=request.POST.get('district_id'),
                    city_id=request.POST.get('city_id'),
                    address=request.POST.get('address'),
                    gst_no=request.POST.get('gst_no'),
                    logo=request.FILES.get('logo'),
                    is_active=False
                )

                messages.success(
                    request,
                    "Project registered successfully. Await admin approval."
                )
                return redirect('login')

        except Exception as e:
            messages.error(request, f"Registration failed: {e}")

    states = State.objects.filter(is_active=True).order_by('name')
    
    return render(request, 'register.html', {
        'states': states
    })

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

def password_reset_view(request):
    """
    Password reset view
    """
    # Redirect to login if user is authenticated
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Add your password reset logic here
    # This is just a placeholder
    return render(request, 'password_reset.html')