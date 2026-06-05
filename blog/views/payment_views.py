from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from ..forms import PaymentForm
from ..models import Order, Payment
from ..utils import get_page_number


@login_required
def payment_add(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    if order.status == 'cancelled':
        messages.warning(request, 'Bekor qilingan buyurtmaga to\'lov qo\'shib bo\'lmaydi.')
        return redirect('order_detail', pk=order.pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, order=order)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.created_by = request.user
            payment.save()
            messages.success(request, 'To\'lov qo\'shildi.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = PaymentForm(initial={'payment_date': timezone.now().date()}, order=order)
    if order.status == 'completed':
        messages.info(request, 'Bu buyurtma tugallangan. Keyingi to\'lovlarni ham qayd etishingiz mumkin.')
    return render(request, 'blog/orders/payment_form.html', {'form': form, 'order': order, 'title': "To'lov qo'shish"})


@login_required
def payment_list(request):
    payments = Payment.objects.select_related('order', 'order__client').order_by('-payment_date')
    paginator = Paginator(payments, 30)
    payments = paginator.get_page(get_page_number(request))
    return render(request, 'blog/payments/list.html', {'payments': payments})


@login_required
def payment_edit(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('order'), pk=pk)
    order = payment.order
    if order.status == 'cancelled':
        messages.warning(request, 'Bekor qilingan buyurtmaning to\'lovini tahrirlab bo\'lmaydi.')
        return redirect('order_detail', pk=order.pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, instance=payment, order=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'To\'lov yangilandi.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = PaymentForm(instance=payment, order=order)
    return render(request, 'blog/orders/payment_form.html', {
        'form': form,
        'order': order,
        'title': 'To\'lovni tahrirlash',
        'payment': payment,
    })


@login_required
@require_POST
def payment_delete(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('order'), pk=pk)
    order = payment.order
    payment.delete()
    messages.success(request, 'To\'lov o\'chirildi.')
    next_url = request.POST.get('next')
    if next_url == 'payment_list':
        return redirect('payment_list')
    return redirect('order_detail', pk=order.pk)
