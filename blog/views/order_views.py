from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from ..forms import OrderForm, OrderWorkerFormSet
from ..models import Client, Order, OrderWorker, ServiceType
from ..utils import get_page_number


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
    orders = paginator.get_page(get_page_number(request))
    return render(request, 'blog/orders/list.html', {
        'orders': orders, 'q': q, 'status': status
    })


def _order_form_context(form, title, order=None, formset=None):
    prices = {str(st.id): float(st.default_price) for st in ServiceType.objects.all()}
    import json
    ctx = {'form': form, 'title': title, 'order': order, 'service_prices': json.dumps(prices)}
    if formset is not None:
        ctx['worker_formset'] = formset
    return ctx


@login_required
def order_create(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderWorkerFormSet(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.created_by = request.user
            order.save()
            formset = OrderWorkerFormSet(request.POST, instance=order)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Buyurtma yaratildi.')
                return redirect('order_detail', pk=order.pk)
            messages.warning(request, 'Buyurtma yaratildi. Ishchilar ma\'lumotida xato — quyida tuzating.')
            return redirect('order_edit', pk=order.pk)
        else:
            formset = OrderWorkerFormSet(request.POST)
    else:
        initial = {}
        client_id = request.GET.get('client')
        if client_id and Client.objects.filter(pk=client_id).exists():
            initial['client'] = client_id
        form = OrderForm(initial=initial)
        formset = OrderWorkerFormSet()
    return render(request, 'blog/orders/form.html', _order_form_context(form, "Buyurtma qo'shish", formset=formset))


@login_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.select_related('client', 'service_type').prefetch_related('order_workers__worker'),
        pk=pk
    )
    return render(request, 'blog/orders/detail.html', {'order': order})


@login_required
def order_edit(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status == 'completed':
        return redirect('order_detail', pk=pk)
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderWorkerFormSet(request.POST, instance=order)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Buyurtma yangilandi.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderWorkerFormSet(instance=order)
    return render(request, 'blog/orders/form.html', _order_form_context(form, "Buyurtmani tahrirlash", order, formset))


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
        messages.success(request, 'Buyurtma tugallandi deb belgilandi.')
    return redirect('order_detail', pk=order.pk)


@login_required
@require_POST
def order_set_status(request, pk):
    """Buyurtma holatini Qoralama <-> Jarayonda o'zgartirish."""
    order = get_object_or_404(Order, pk=pk)
    if order.status in ('completed', 'cancelled'):
        return redirect('order_detail', pk=order.pk)
    new_status = request.POST.get('status')
    if new_status in ('draft', 'in_progress'):
        old_display = order.get_status_display()
        order.status = new_status
        order.save(update_fields=['status', 'updated_at'])
        from ..models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='update',
            model_name='Order',
            object_id=order.pk,
            object_repr=str(order)[:200],
            changes={'status': f'{old_display} → {order.get_status_display()}'},
        )
        messages.success(request, f"Holat «{order.get_status_display()}» ga o'zgartirildi.")
    return redirect('order_detail', pk=order.pk)


@login_required
@require_POST
def order_cancel(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if order.status not in ('completed', 'cancelled'):
        order.mark_cancelled()
        from ..models import ActivityLog
        ActivityLog.objects.create(
            user=request.user,
            action='update',
            model_name='Order',
            object_id=order.pk,
            object_repr=str(order)[:200],
            changes={'status': 'Bekor qilindi'},
        )
        messages.success(request, 'Buyurtma bekor qilindi.')
    return redirect('order_detail', pk=order.pk)


@login_required
def order_copy(request, pk):
    """Mavjud buyurtmani nusxalash — yangi buyurtma shu ma'lumotlar bilan yaratiladi."""
    order = get_object_or_404(Order.objects.select_related('client', 'service_type'), pk=pk)
    new_order = Order(
        client=order.client,
        description=order.description,
        service_type=order.service_type,
        quantity=order.quantity,
        total_price=order.total_price,
        deadline=order.deadline,
        debt_payment_deadline=order.debt_payment_deadline,
        status='draft',
        created_by=request.user,
    )
    new_order.save()
    for ow in order.order_workers.select_related('worker').all():
        OrderWorker.objects.create(order=new_order, worker=ow.worker, share_percent=ow.share_percent)
    messages.success(request, f'Buyurtma nusxalandi: {new_order.order_number}')
    return redirect('order_edit', pk=new_order.pk)


@login_required
def order_print(request, pk):
    order = get_object_or_404(Order.objects.select_related('client', 'service_type'), pk=pk)
    return render(request, 'blog/orders/print.html', {'order': order})
