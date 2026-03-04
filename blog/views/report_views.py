from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Sum
from django.shortcuts import render
from django.utils import timezone
from collections import defaultdict
from ..models import Client, Expense, Order, OrderWorker, Payment
from ..utils import get_page_number


@login_required
def dashboard(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    today_sales = Payment.objects.filter(payment_date=today).aggregate(s=Sum('amount'))['s'] or 0
    week_sales = Payment.objects.filter(payment_date__gte=week_start).aggregate(s=Sum('amount'))['s'] or 0

    debtors = Client.objects.filter(
        orders__status__in=['draft', 'in_progress', 'completed']
    ).distinct()
    total_debt = sum(c.total_debt for c in debtors)

    upcoming_deadlines = Order.objects.filter(
        status__in=['draft', 'in_progress'],
        deadline__gte=today,
        deadline__lte=today + timedelta(days=7)
    ).select_related('client').order_by('deadline')[:10]

    recent_payments = Payment.objects.select_related(
        'order', 'order__client'
    ).order_by('-payment_date')[:5]

    recent_orders = Order.objects.select_related('client').order_by('-created_at')[:8]
    today_orders = Order.objects.filter(
        status__in=['draft', 'in_progress'],
        created_at__date=today
    ).select_related('client').order_by('-created_at')[:5]

    month_start = today.replace(day=1)
    today_expenses = Expense.objects.filter(expense_date=today).aggregate(s=Sum('amount'))['s'] or 0
    month_expenses = Expense.objects.filter(expense_date__gte=month_start).aggregate(s=Sum('amount'))['s'] or 0
    recent_expenses = Expense.objects.order_by('-expense_date')[:5]

    # Bu oy ishchilarning hisoblangan oyligi (tugallangan buyurtmalar bo'yicha)
    month_order_workers = OrderWorker.objects.filter(
        order__status='completed',
        order__created_at__date__gte=month_start,
        order__created_at__date__lte=today,
    ).select_related('order')
    month_salary = sum(float(ow.order.total_price) * float(ow.share_percent) / 100 for ow in month_order_workers)

    unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, 'blog/dashboard.html', {
        'today_sales': today_sales,
        'week_sales': week_sales,
        'total_debt': total_debt,
        'today_expenses': today_expenses,
        'month_expenses': month_expenses,
        'month_salary': month_salary,
        'upcoming_deadlines': upcoming_deadlines,
        'recent_payments': recent_payments,
        'recent_orders': recent_orders,
        'recent_expenses': recent_expenses,
        'today_orders': today_orders,
        'unread_count': unread_count,
    })


@login_required
def report_sales(request):
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    today = timezone.now().date()

    if from_date:
        from_date = __parse_date(from_date) or today - timedelta(days=30)
    else:
        from_date = today - timedelta(days=30)

    if to_date:
        to_date = __parse_date(to_date) or today
    else:
        to_date = today

    payments_qs = Payment.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date
    ).select_related('order', 'order__client', 'order__service_type').order_by('-payment_date')

    total = payments_qs.aggregate(s=Sum('amount'))['s'] or 0

    by_service = {}
    for p in payments_qs:
        key = p.order.service_type.name if p.order.service_type else 'Boshqa'
        by_service[key] = by_service.get(key, 0) + float(p.amount)
    by_service = dict(sorted(by_service.items(), key=lambda x: -x[1]))

    paginator = Paginator(payments_qs, 30)
    payments_page = paginator.get_page(get_page_number(request))

    return render(request, 'blog/reports/sales.html', {
        'payments': payments_page,
        'page_obj': payments_page,
        'total': total,
        'from_date': from_date,
        'to_date': to_date,
        'by_service': by_service,
    })


@login_required
def report_debts(request):
    today = timezone.now().date()
    debtors = []
    seen = set()

    orders_qs = Order.objects.filter(
        status__in=['draft', 'in_progress', 'completed']
    ).select_related('client').order_by(
        F('debt_payment_deadline').asc(nulls_last=True)
    )
    for order in orders_qs:
        if order.remaining_debt <= 0 or order.client_id in seen:
            continue
        seen.add(order.client_id)
        client_debt = order.client.total_debt
        dl = order.debt_payment_deadline
        debtors.append({
            'client': order.client,
            'debt': client_debt,
            'deadline': dl,
            'days_left': (dl - today).days if dl else None,
        })

    total_debt = sum(float(d['debt']) for d in debtors)
    debtors.sort(key=lambda x: (x['days_left'] if x['days_left'] is not None else 999, -float(x['debt'])))

    paginator = Paginator(debtors, 25)
    debtors_page = paginator.get_page(get_page_number(request))

    return render(request, 'blog/reports/debts.html', {
        'debtors': debtors_page,
        'page_obj': debtors_page,
        'total_debt': total_debt,
        'today': today,
    })


@login_required
def salary_report(request):
    """Oylik ish haqi: tugallangan buyurtmalar bo'yicha ishchilarning ulushi (ishbay)."""
    today = timezone.now().date()
    year = request.GET.get('year')
    month = request.GET.get('month')
    try:
        year = int(year) if year else today.year
        month = int(month) if month else today.month
    except (TypeError, ValueError):
        year, month = today.year, today.month
    if month < 1 or month > 12:
        month = today.month
    # Oy oralig'i
    from calendar import monthrange
    _, last_day = monthrange(year, month)
    from datetime import date
    start = date(year, month, 1)
    end = date(year, month, last_day)

    order_workers = OrderWorker.objects.filter(
        order__status='completed',
        order__created_at__date__gte=start,
        order__created_at__date__lte=end,
    ).select_related('order', 'worker')

    by_worker = defaultdict(lambda: 0)
    for ow in order_workers:
        amount = float(ow.order.total_price) * float(ow.share_percent) / 100
        by_worker[ow.worker] += amount

    rows = [{'worker': w, 'total': total} for w, total in sorted(by_worker.items(), key=lambda x: -x[1])]
    total_salary = sum(r['total'] for r in rows)

    months_uz = ['', 'Yanvar', 'Fevral', 'Mart', 'Aprel', 'May', 'Iyun', 'Iyul', 'Avgust', 'Sentabr', 'Oktabr', 'Noyabr', 'Dekabr']
    month_name = months_uz[month] if 1 <= month <= 12 else str(month)
    months_choices = [(i, months_uz[i]) for i in range(1, 13)]

    return render(request, 'blog/reports/salary.html', {
        'rows': rows,
        'total_salary': total_salary,
        'year': year,
        'month': month,
        'month_name': month_name,
        'months_choices': months_choices,
    })


def __parse_date(s):
    try:
        from datetime import datetime
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
