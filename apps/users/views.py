from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from apps.subunits.models import (
    SuRole, UserHasSuRole,
    UserHasSuState, UserHasSuDistrict, UserHasSuCity
)
from apps.subunits.models import Subunit
from apps.masters.states.models import State
from apps.masters.districts.models import District
from apps.masters.city.models import City
from apps.masters.designations.models import Designation

User = get_user_model()


# ---------------------------------------
# Permission Mixin
# ---------------------------------------
class AdminOnlyMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff


# ---------------------------------------
# SINGLE USER CONTROLLER
# ---------------------------------------
class UserView(LoginRequiredMixin, AdminOnlyMixin, View):
    list_template = "user_list.html"
    form_template = "user_form.html"

    # -------------------------
    # GET HANDLER
    # -------------------------
    def get(self, request, pk=None):
        if "create" in request.path:
            return self.user_form(request)

        if pk and "edit" in request.path:
            return self.user_form(request, pk)

        if pk and "delete" in request.path:
            return self.delete_user(request, pk)

        return self.user_list(request)

    # -------------------------
    # POST HANDLER
    # -------------------------
    def post(self, request, pk=None):
        if pk:
            return self.save_user(request, pk)
        return self.save_user(request)

    # =====================================================
    # LIST USERS WITH FILTERS + PAGINATION
    # =====================================================
    def user_list(self, request):
        search = request.GET.get("search", "")
        role = request.GET.get("role", "")
        status = request.GET.get("status", "")

        users = User.objects.all()

        # Search filter
        if search:
            users = users.filter(
                Q(username__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        # Role filter
        if role == "admin":
            users = users.filter(is_superuser=True)
        elif role == "staff":
            users = users.filter(is_staff=True)


        users = users.order_by("-id")

        # # Pagination
        # paginator = Paginator(users, 10)  # 10 per page
        # page_number = request.GET.get("page")
        # users = paginator.get_page(page_number)

        return render(request, self.list_template, {
            "users": users,
            "search": search,
            "role": role,
            "status": status,
        })

    # =====================================================
    # CREATE / EDIT FORM
    # =====================================================
    def user_form(self, request, pk=None):
        user = None
        if pk:
            user = get_object_or_404(User, pk=pk)

        context = {
            "user_obj": user,
            "subunits": Subunit.objects.all(),
            "roles": SuRole.objects.all(),
            "states": State.objects.order_by("name").all(),
            "districts": District.objects.order_by("name").all(),
            "cities": City.objects.order_by("name").all(),
            "designations": Designation.objects.filter(is_active=True).order_by("name")
        }

        return render(request, self.form_template, context)

    # =====================================================
    # SAVE USER (CREATE + UPDATE)
    # =====================================================
    def save_user(self, request, pk=None):
        name = request.POST.get("name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")
        password = request.POST.get("password")
        is_staff = bool(request.POST.get("is_staff"))
        is_active = bool(request.POST.get("is_active"))
        role_id = request.POST.get("role")
        subunit_id = request.POST.get("subunit_id")
        designation_id = request.POST.get("designation_id")

        states = request.POST.getlist("states")
        districts = request.POST.getlist("districts")
        cities = request.POST.getlist("cities")


        if pk:
            user = get_object_or_404(User, pk=pk)
        else:
            user = User()

        user.first_name = name
        user.username = username
        user.email = email
        user.mobile = mobile
        user.is_staff = is_staff
        user.is_active = is_active
        user.designation_id = designation_id

        if password:
            user.set_password(password)

        user.save()
        
        # -------------------------
        # ASSIGN ROLE
        # -------------------------
        if role_id and subunit_id:
            UserHasSuRole.objects.update_or_create(
                user=user,
                subunit_id=subunit_id,
                defaults={"role_id": role_id}
            )

        if subunit_id:
            # RESET GEO
            UserHasSuState.objects.filter(user=user, subunit_id=subunit_id).delete()
            UserHasSuDistrict.objects.filter(user=user, subunit_id=subunit_id).delete()
            UserHasSuCity.objects.filter(user=user, subunit_id=subunit_id).delete()

            # SAVE STATES
            for sid in states:
                UserHasSuState.objects.create(user=user, subunit_id=subunit_id, state_id=sid)

            # SAVE DISTRICTS
            for did in districts:
                UserHasSuDistrict.objects.create(user=user, subunit_id=subunit_id, district_id=did)

            # SAVE CITIES
            for cid in cities:
                UserHasSuCity.objects.create(user=user, subunit_id=subunit_id, city_id=cid)
        
        messages.success(request, "User saved successfully")
        return redirect("user_list")

    # =====================================================
    # DELETE USER
    # =====================================================
    def delete_user(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        messages.success(request, "User deleted")
        return redirect("user_list")
