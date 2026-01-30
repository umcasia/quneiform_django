from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import City
from apps.masters.states.models import State
from apps.masters.districts.models import District
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin

class Cities(LoginRequiredMixin, View):
    @login_required
    def city_list(request):
        states = State.objects.order_by('name').all()
        search = request.GET.get('search', '').strip()
        status = request.GET.get('status')
        state_id = request.GET.get('state')
        district_id = request.GET.get('district')

        districts = District.objects.none()
        cities = City.objects.select_related('district', 'district__state').order_by('name')

        if search:
            cities = cities.filter(name__icontains=search)
        if state_id:
            # cities = cities.filter(state_id=state_id)
            districts = District.objects.filter(state_id=state_id).order_by('name')
            cities = cities.filter(district__state_id=state_id)
        if district_id:
            cities = cities.filter(district_id=district_id)

        paginator = Paginator(cities, 10)
        page_obj = paginator.get_page(request.GET.get('page', 1))

        return render(request, 'city_list.html', {
            'cities': page_obj,
            'states': states,
            'districts': districts,
            'search': search,
            'status': status,
            'state_id': state_id,
            'district_id': district_id,
        })

    @login_required
    def city_create(request):
        if request.method == 'POST':
            City.objects.create(
                name=request.POST['name'],
                district_id=request.POST['district'],
                is_active=bool(request.POST.get('is_active'))
            )
            messages.success(request, 'City created successfully')
        return redirect('city-list')

    @login_required
    def city_edit(request, pk):
        city = get_object_or_404(City, pk=pk)

        if request.method == 'POST':
            city.name = request.POST['name']
            city.district_id = request.POST['district']
            city.is_active = bool(request.POST.get('is_active'))
            city.save()
            messages.success(request, 'City updated successfully')

        return redirect('city-list')

    @login_required
    def city_delete(request, pk):
        city = get_object_or_404(City, pk=pk)
        city.delete()
        messages.success(request, 'City deleted successfully')
        return redirect('city-list')

    def get_cities_by_district(request):

        # Multi-select
        district_ids = request.GET.getlist("district_ids[]")

        # Single select
        district_id = request.GET.get("district_id")

        if district_ids:
            # DO NOT split (already list)
            cities = City.objects.filter(district_id__in=district_ids)

        elif district_id:
            cities = City.objects.filter(district_id=district_id)

        else:
            return JsonResponse([], safe=False)

        data = list(cities.values("city_id", "name"))
        return JsonResponse(data, safe=False)
