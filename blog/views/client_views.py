from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from ..forms import ClientForm
from ..models import Client


@login_required
def client_list(request):
    q = request.GET.get('q', '')
    clients = Client.objects.all()
    if q:
        clients = clients.filter(Q(full_name__icontains=q) | Q(phone__icontains=q))
    clients = clients.order_by('-created_at')
    paginator = Paginator(clients, 20)
    page = request.GET.get('page', 1)
    clients = paginator.get_page(page)
    return render(request, 'blog/clients/list.html', {'clients': clients, 'q': q})


@login_required
def client_create(request):
    if request.method == 'POST':
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            client.created_by = request.user
            client.save()
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm()
    return render(request, 'blog/clients/form.html', {'form': form, 'title': 'Mijoz qo\'shish'})


@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, 'blog/clients/detail.html', {'client': client})


@login_required
def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            return redirect('client_detail', pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(request, 'blog/clients/form.html', {'form': form, 'title': 'Mijozni tahrirlash', 'client': client})
