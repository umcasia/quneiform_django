from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Designation
from django.contrib.auth.decorators import login_required

@login_required
def designation_list(request):
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', '')

    designations = Designation.objects.all()

    if search:
        designations = designations.filter(name__icontains=search)

    if status == 'active':
        designations = designations.filter(is_active=True)
    elif status == 'inactive':
        designations = designations.filter(is_active=False)

    paginator = Paginator(designations, 10)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'designation_list.html', {
        'designations': page_obj,
        'search': search,
        'status': status,
    })

@login_required
def designation_create(request):
    if request.method == 'POST':
        designation, created = Designation.objects.get_or_create(
            name=request.POST['name'].strip(),
            is_active=bool(request.POST.get('is_active'))
        )
        
        if created:
            messages.success(request, "Designation created")
        else:
            messages.warning(request, "Designation already exists")
    
    return redirect('designation-list')

@login_required
def designation_edit(request, pk):
    designation = get_object_or_404(Designation, pk=pk)

    if request.method == 'POST':
        designation.name = request.POST['name']
        designation.is_active = bool(request.POST.get('is_active'))
        designation.save()
        messages.success(request, 'Designation updated successfully')

    return redirect('designation-list')

@login_required
def designation_delete(request, pk):
    designation = get_object_or_404(Designation, pk=pk)
    designation.delete()
    messages.success(request, 'Designation deleted successfully')
    return redirect('designation-list')
