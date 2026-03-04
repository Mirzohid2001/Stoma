from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from ..forms import WorkerForm
from ..models import Worker


@login_required
def worker_list(request):
    workers = Worker.objects.all().order_by('full_name')
    return render(request, 'blog/workers/list.html', {'workers': workers})


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
def worker_delete(request, pk):
    worker = get_object_or_404(Worker, pk=pk)
    worker.delete()
    messages.success(request, 'Ishchi o\'chirildi.')
    return redirect('worker_list')
