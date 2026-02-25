from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from ..models import ClinicSettings, Payment


@login_required
def payment_receipt(request, pk):
    payment = get_object_or_404(Payment.objects.select_related('order', 'order__client'), pk=pk)
    clinic = ClinicSettings.objects.first()
    return render(request, 'blog/receipt.html', {'payment': payment, 'clinic': clinic})
