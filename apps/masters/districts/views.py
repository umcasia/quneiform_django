from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from apps.masters.districts.models import District
from apps.masters.states.models import State
from django.contrib.auth.decorators import login_required

@login_required
def district_list(request):
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')
    state_id = request.GET.get('state')

    districts = District.objects.select_related('state')

    if search:
        districts = districts.filter(name__icontains=search)

    if state_id:
        districts = districts.filter(state_id=state_id)

    if status == 'active':
        districts = districts.filter(is_active=True)
    elif status == 'inactive':
        districts = districts.filter(is_active=False)

    paginator = Paginator(districts, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'district_list.html', {
        'districts': page_obj,
        'states': State.objects.all(),
        'search': search,
        'status': status,
        'state_id': state_id,
    })

@login_required
def district_create(request):
    if request.method == 'POST':
        District.objects.create(
            name=request.POST['name'],
            state_id=request.POST['state'],
            is_active=bool(request.POST.get('is_active'))
        )
        messages.success(request, 'District created successfully')
    return redirect('district-list')

@login_required
def district_edit(request, pk):
    district = get_object_or_404(District, pk=pk)

    if request.method == 'POST':
        district.name = request.POST['name']
        district.state_id = request.POST['state']
        district.is_active = bool(request.POST.get('is_active'))
        district.save()
        messages.success(request, 'District updated successfully')

    return redirect('district-list')

@login_required
def district_delete(request, pk):
    district = get_object_or_404(District, pk=pk)
    district.delete()
    messages.success(request, 'District deleted successfully')
    return redirect('district-list')

def get_districts_by_state(request):
    state_id = request.GET.get('state_id')
    districts = District.objects.filter(state_id=state_id).values('district_id', 'name')
    return JsonResponse(list(districts), safe=False)