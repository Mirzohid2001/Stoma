from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import ServiceTypeForm
from ..models import ServiceType
from ..utils import get_page_number


@login_required
def servicetype_list(request):
    qs = ServiceType.objects.all().order_by('name')
    paginator = Paginator(qs, 15)
    items = paginator.get_page(get_page_number(request))
    return render(request, 'blog/servicetypes/list.html', {'items': items, 'page_obj': items})


@login_required
def servicetype_create(request):
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Xizmat turi qo\'shildi.')
            return redirect('servicetype_list')
    else:
        form = ServiceTypeForm()
    return render(request, 'blog/servicetypes/form.html', {'form': form, 'title': "Xizmat turini qo'shish"})


@login_required
def servicetype_edit(request, pk):
    item = get_object_or_404(ServiceType, pk=pk)
    if request.method == 'POST':
        form = ServiceTypeForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Xizmat turi yangilandi.')
            return redirect('servicetype_list')
    else:
        form = ServiceTypeForm(instance=item)
    return render(request, 'blog/servicetypes/form.html', {'form': form, 'title': "Xizmat turini tahrirlash", 'item': item})


@login_required
@require_POST
def servicetype_delete(request, pk):
    item = get_object_or_404(ServiceType, pk=pk)
    item.delete()
    messages.success(request, 'Xizmat turi o\'chirildi.')
    return redirect('servicetype_list')
