from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from ..forms import PaymentForm
from ..models import Order, Payment


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
            return redirect('order_detail', pk=order.pk)
    else:
        form = PaymentForm(initial={'payment_date': timezone.now().date()})
    return render(request, 'blog/orders/payment_form.html', {'form': form, 'order': order})


@login_required
def payment_list(request):
    payments = Payment.objects.select_related('order', 'order__client').order_by('-payment_date')
    paginator = Paginator(payments, 30)
    page = request.GET.get('page', 1)
    payments = paginator.get_page(page)
    return render(request, 'blog/payments/list.html', {'payments': payments})
