from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import permission_required
from .models import State
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required

@login_required
# @permission_required('masters.view_state', raise_exception=True)
def state_list(request):
    states = State.objects.all()

    # GET filters
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status')

    if search:
        states = states.filter(name__icontains=search)

    if status == 'active':
        states = states.filter(is_active=True)
    elif status == 'inactive':
        states = states.filter(is_active=False)
        
    paginator = Paginator(states, 10)  # 10 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'state_list.html', {
        'states': page_obj,
        'search': search,
        'status': status,
    })
@login_required 
# @permission_required('masters.add_state', raise_exception=True)
def state_create(request):
    if request.method == 'POST':
        state, created = State.objects.get_or_create(
            name=request.POST['name'].strip(),
            is_active=True if request.POST.get('is_active') else False
        )
        
        
        if created:
            messages.success(request, "State created successfully")
        else:
            messages.warning(request, "Designation already exists")
        
    return redirect('state-list')
@login_required
# @permission_required('masters.change_state', raise_exception=True)
def state_edit(request, pk):
    state = get_object_or_404(State, pk=pk)

    if request.method == 'POST':
        state.name = request.POST.get('name')
        state.is_active = True if request.POST.get('is_active') else False
        state.save()

    return redirect('state-list')
@login_required
# @permission_required('masters.delete_state', raise_exception=True)
def state_delete(request, pk):
    state = get_object_or_404(State, pk=pk)
    state.delete()   # ✅ HARD DELETE
    messages.success(request, "State deleted successfully")
    return redirect('state-list')

