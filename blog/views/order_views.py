from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from ..forms import OrderForm
from ..models import Order


@login_required
def order_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')
    orders = Order.objects.select_related('client').all()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(client__full_name__icontains=q) |
            Q(client__phone__icontains=q)
        )
    if status:
        orders = orders.filter(status=status)
    orders = orders.order_by('-created_at')
    paginator = Paginator(orders, 20)
    page = request.GET.get('page', 1)
    orders = paginator.get_page(page)
    return render(request, 'blog/orders/list.html', {
        'orders': orders, 'q': q, 'status': status
    })


@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            return redirect('order_detail', pk=order.pk)
    else:
        initial = {}
        if client_id := request.GET.get('client'):
            initial['client'] = client_id
        form = OrderForm(initial=initial)
    return render(request, 'blog/orders/form.html', {'form': form, 'title': 'Buyurtma qo\'shish'})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('client', 'service_type'), pk=pk)
    return render(request, 'blog/orders/detail.html', {'order': order})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status == 'completed':
        return redirect('order_detail', pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
    return render(request, 'blog/orders/form.html', {
        'form': form, 'title': 'Buyurtmani tahrirlash', 'order': order
    })


@login_required
@require_POST
def order_complete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status != 'completed':
        order.mark_completed()
        from ..models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='complete',
            model_name='Order',
            object_id=order.pk,
            object_repr=str(order)[:200],
        )
    return redirect('order_detail', pk=pk)
