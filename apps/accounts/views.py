from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.contrib.auth import get_user_model

from apps.projects.models import Project
from apps.masters.states.models import State
from apps.masters.designations.models import Designation

User = get_user_model()


class LoginView(View):
    template_name = "login.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("dashboard")

        messages.error(request, "Invalid username or password")
        return render(request, self.template_name)


class RegisterView(View):
    template_name = "register.html"

    def get(self, request):
        states = State.objects.filter(is_active=True).order_by("name")
        designations = Designation.objects.filter(is_active=True).order_by("name")
        return render(request, self.template_name, {
            "states": states,
            "designations": designations
        })

    def post(self, request):
        try:
            with transaction.atomic():
                Project.objects.create(
                    name=request.POST.get("org_name"),
                    email=request.POST.get("email"),
                    contact_person=request.POST.get("contact_person"),
                    designation_id=request.POST.get("designation_id"),
                    mobile=request.POST.get("mobile"),
                    state_id=request.POST.get("state_id"),
                    district_id=request.POST.get("district_id"),
                    city_id=request.POST.get("city_id"),
                    address=request.POST.get("address"),
                    gst_no=request.POST.get("gst_no"),
                    logo=request.FILES.get("logo"),
                    is_active=False,
                )

            messages.success(
                request,
                "Project registered successfully. Await admin approval."
            )
            return redirect("login")

        except Exception as e:
            messages.error(request, f"Registration failed: {e}")
            return redirect("register")


class LogoutView(LoginRequiredMixin, View):

    def get(self, request):
        logout(request)
        return redirect("login")


class PasswordResetView(View):
    template_name = "password_reset.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("dashboard")
        return render(request, self.template_name)
