from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from ..models import Client, Order, Payment


@login_required
def report_analytics(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    daily = Payment.objects.filter(payment_date=today).aggregate(s=Sum('amount'))['s'] or 0
    weekly = Payment.objects.filter(payment_date__gte=week_start).aggregate(s=Sum('amount'))['s'] or 0
    monthly = Payment.objects.filter(payment_date__gte=month_start).aggregate(s=Sum('amount'))['s'] or 0

    clients_with_payments = Client.objects.filter(orders__payments__isnull=False).distinct()
    top_clients = []
    for c in clients_with_payments:
        spent = c.total_spent
        if spent > 0:
            top_clients.append({'client': c, 'spent': spent})
    top_clients.sort(key=lambda x: -float(x['spent']))
    top_clients = top_clients[:10]

    by_status = {}
    for status, label in Order.STATUS_CHOICES:
        by_status[label] = Order.objects.filter(status=status).count()

    upcoming = Order.objects.filter(
        status__in=['draft', 'in_progress'],
        deadline__gte=today,
        deadline__lte=today + timedelta(days=7)
    ).count()

    return render(request, 'blog/reports/analytics.html', {
        'daily': daily,
        'weekly': weekly,
        'monthly': monthly,
        'top_clients': top_clients,
        'by_status': by_status,
        'upcoming': upcoming,
    })
