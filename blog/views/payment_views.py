from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from ..forms import PaymentForm
from ..models import Order, Payment
from ..utils import get_page_number


@login_required
def payment_add(request, order_pk):
    order = get_object_or_404(Order, pk=order_pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.created_by = request.user
            payment.save()
            messages.success(request, 'To\'lov qo\'shildi.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = PaymentForm(initial={'payment_date': timezone.now().date()})
    if order.status == 'completed':
        messages.info(request, 'Bu buyurtma tugallangan. Keyingi to\'lovlarni ham qayd etishingiz mumkin.')
    return render(request, 'blog/orders/payment_form.html', {'form': form, 'order': order})


@login_required
def payment_list(request):
    payments = Payment.objects.select_related('order', 'order__client').order_by('-payment_date')
    paginator = Paginator(payments, 30)
    payments = paginator.get_page(get_page_number(request))
    return render(request, 'blog/payments/list.html', {'payments': payments})
