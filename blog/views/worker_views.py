from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import WorkerForm
from ..models import Worker
from ..utils import get_page_number


@login_required
def worker_list(request):
    qs = Worker.objects.all().order_by('full_name')
    paginator = Paginator(qs, 25)
    workers = paginator.get_page(get_page_number(request))
    return render(request, 'blog/workers/list.html', {'workers': workers, 'page_obj': workers})


@login_required
def worker_create(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ishchi qo\'shildi.')
            return redirect('worker_list')
    else:
        form = WorkerForm()
    return render(request, 'blog/workers/form.html', {'form': form, 'title': 'Ishchi qo\'shish'})


@login_required
def worker_edit(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Ishchi yangilandi.')
            return redirect('worker_list')
    else:
        form = WorkerForm(instance=worker)
    return render(request, 'blog/workers/form.html', {'form': form, 'title': 'Ishchini tahrirlash', 'worker': worker})


@login_required
@require_POST
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.delete()
    messages.success(request, 'Ishchi o\'chirildi.')
    return redirect('worker_list')
