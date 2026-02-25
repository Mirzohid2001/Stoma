from calendar import Calendar
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from ..models import Order


@login_required
def calendar_view(request):
    year = int(request.GET.get('year', timezone.now().year))
    month = int(request.GET.get('month', timezone.now().month))

    cal = Calendar(firstweekday=0)
    weeks = list(cal.monthdatescalendar(year, month))

    orders_by_date = {}
    for o in Order.objects.filter(
        status__in=['draft', 'in_progress'],
        deadline__isnull=False
    ).filter(deadline__year=year, deadline__month=month).select_related('client'):
        d = o.deadline
        if d not in orders_by_date:
            orders_by_date[d] = []
        orders_by_date[d].append(o)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    return render(request, 'blog/calendar.html', {
        'weeks': weeks,
        'year': year,
        'month': month,
        'orders_by_date': orders_by_date,
        'prev': {'year': prev_year, 'month': prev_month},
        'next': {'year': next_year, 'month': next_month},
    })
