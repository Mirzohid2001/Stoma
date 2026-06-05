from calendar import monthrange
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from collections import defaultdict
from ..models import Client, Expense, Order, OrderWorker, Payment
from ..utils import build_debtors_list, get_page_number, parse_date, resolve_profit_loss_dates


def compute_profit_loss(from_date, to_date):
    """Berilgan davr uchun daromad, rasxod, ish haqi va sof foydani hisoblaydi."""
    revenue = Payment.objects.filter(
        payment_date__gte=from_date,
        payment_date__lte=to_date,
    ).aggregate(s=Sum('amount'))['s'] or 0
    expense_amount = Expense.objects.filter(
        expense_date__gte=from_date,
        expense_date__lte=to_date,
    ).aggregate(s=Sum('amount'))['s'] or 0
    salary_rows = OrderWorker.objects.filter(
        order__status='completed',
        order__completed_at__date__gte=from_date,
        order__completed_at__date__lte=to_date,
    ).select_related('order')
    salary = sum(float(ow.order.total_price) * float(ow.share_percent) / 100 for ow in salary_rows)

    total_expense = float(expense_amount) + float(salary)
    net_profit = float(revenue) - total_expense
    margin = (net_profit / float(revenue) * 100) if float(revenue) else 0

    return {
        'revenue': revenue,
        'expense_amount': expense_amount,
        'salary': salary,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'margin': margin,
    }


def _month_bounds(anchor_date):
    last_day = monthrange(anchor_date.year, anchor_date.month)[1]
    return date(anchor_date.year, anchor_date.month, 1), date(anchor_date.year, anchor_date.month, last_day)


def _shift_month(anchor_date, delta_months):
    year = anchor_date.year
    month = anchor_date.month + delta_months
    while month <= 0:
        month += 12
        year -= 1
    while month > 12:
        month -= 12
        year += 1
    return date(year, month, 1)


def _monthly_financial_series(today, months=6):
    labels = []
    revenue_data = []
    expense_data = []
    profit_data = []
    expense_map = {}
    salary_map = {}

    base = today.replace(day=1)
    for offset in range(months - 1, -1, -1):
        probe = _shift_month(base, -offset)
        month_start, month_end = _month_bounds(probe)
        key = month_start.strftime('%Y-%m')
        expense_map[key] = float(
            Expense.objects.filter(expense_date__gte=month_start, expense_date__lte=month_end).aggregate(s=Sum('amount'))['s'] or 0
        )
        salary_rows = OrderWorker.objects.filter(
            order__status='completed',
            order__completed_at__date__gte=month_start,
            order__completed_at__date__lte=month_end,
        ).select_related('order')
        salary_map[key] = sum(float(ow.order.total_price) * float(ow.share_percent) / 100 for ow in salary_rows)

    for offset in range(months - 1, -1, -1):
        probe = _shift_month(base, -offset)
        month_start, month_end = _month_bounds(probe)
        key = month_start.strftime('%Y-%m')

        revenue = float(
            Payment.objects.filter(payment_date__gte=month_start, payment_date__lte=month_end).aggregate(s=Sum('amount'))['s'] or 0
        )
        total_expense = expense_map[key] + salary_map[key]
        profit = revenue - total_expense

        labels.append(month_start.strftime('%b %Y'))
        revenue_data.append(round(revenue, 2))
        expense_data.append(round(total_expense, 2))
        profit_data.append(round(profit, 2))

    return labels, revenue_data, expense_data, profit_data


@login_required
def dashboard(request):
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    trend_days = request.GET.get('trend_days', '7')
    if trend_days not in {'7', '30', '90'}:
        trend_days = '7'
    trend_days_int = int(trend_days)

    today_sales = Payment.objects.filter(payment_date=today).aggregate(s=Sum('amount'))['s'] or 0
    week_sales = Payment.objects.filter(payment_date__gte=week_start).aggregate(s=Sum('amount'))['s'] or 0

    debtors = Client.objects.filter(
        orders__status__in=['draft', 'in_progress', 'completed']
    ).distinct()
    total_debt = sum(c.total_debt for c in debtors)

    # Muddati o'tgan (kechikkan) — draft/in_progress, deadline bugundan oldin
    overdue_deadlines = Order.objects.filter(
        status__in=['draft', 'in_progress'],
        deadline__lt=today,
        deadline__isnull=False,
    ).select_related('client').order_by('deadline')[:5]

    # Yaqin muddatlar — bugundan keyingi 7 kun ichida
    upcoming_deadlines = Order.objects.filter(
        status__in=['draft', 'in_progress'],
        deadline__gte=today,
        deadline__lte=today + timedelta(days=7),
        deadline__isnull=False,
    ).select_related('client').order_by('deadline')[:10]

    tomorrow = today + timedelta(days=1)

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

    # Oylik daromad = shu oydagi to'lovlar (kirim)
    month_revenue = Payment.objects.filter(
        payment_date__gte=month_start,
        payment_date__lte=today,
    ).aggregate(s=Sum('amount'))['s'] or 0

    # Bu oy ishchilarning hisoblangan oyligi (tugallangan buyurtmalar bo'yicha)
    month_order_workers = OrderWorker.objects.filter(
        order__status='completed',
        order__completed_at__date__gte=month_start,
        order__completed_at__date__lte=today,
    ).select_related('order')
    month_salary = sum(float(ow.order.total_price) * float(ow.share_percent) / 100 for ow in month_order_workers)

    # Jami rasxod (oylik) = rasxodlar + ish haqi
    total_month_expense = float(month_expenses) + float(month_salary)
    # Sof foyda = daromad - rasxod
    month_net_profit = float(month_revenue) - total_month_expense

    chart_start = today - timedelta(days=trend_days_int - 1)
    daily_revenue = {
        row['payment_date']: float(row['s'] or 0)
        for row in Payment.objects.filter(payment_date__gte=chart_start, payment_date__lte=today)
        .values('payment_date')
        .annotate(s=Sum('amount'))
    }
    daily_expense = {
        row['expense_date']: float(row['s'] or 0)
        for row in Expense.objects.filter(expense_date__gte=chart_start, expense_date__lte=today)
        .values('expense_date')
        .annotate(s=Sum('amount'))
    }
    trend_labels = []
    trend_revenue = []
    trend_expenses = []
    for i in range(trend_days_int):
        day = chart_start + timedelta(days=i)
        trend_labels.append(day.strftime('%d.%m'))
        trend_revenue.append(round(daily_revenue.get(day, 0), 2))
        trend_expenses.append(round(daily_expense.get(day, 0), 2))

    category_rows = (
        Expense.objects.filter(expense_date__gte=month_start, expense_date__lte=today)
        .values('category__name')
        .annotate(s=Sum('amount'))
        .order_by('-s')
    )
    expense_category_labels = []
    expense_category_data = []
    for row in category_rows:
        expense_category_labels.append(row['category__name'] or 'Noma\'lum')
        expense_category_data.append(round(float(row['s'] or 0), 2))
    if month_salary > 0:
        expense_category_labels.append('Ish haqi')
        expense_category_data.append(round(float(month_salary), 2))

    unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, 'blog/dashboard.html', {
        'today_sales': today_sales,
        'week_sales': week_sales,
        'total_debt': total_debt,
        'today_expenses': today_expenses,
        'month_expenses': month_expenses,
        'month_salary': month_salary,
        'month_revenue': month_revenue,
        'total_month_expense': total_month_expense,
        'month_net_profit': month_net_profit,
        'overdue_deadlines': overdue_deadlines,
        'upcoming_deadlines': upcoming_deadlines,
        'today': today,
        'tomorrow': tomorrow,
        'recent_payments': recent_payments,
        'recent_orders': recent_orders,
        'recent_expenses': recent_expenses,
        'today_orders': today_orders,
        'unread_count': unread_count,
        'trend_labels': trend_labels,
        'trend_revenue': trend_revenue,
        'trend_expenses': trend_expenses,
        'expense_category_labels': expense_category_labels,
        'expense_category_data': expense_category_data,
        'trend_days': trend_days,
    })


@login_required
def report_sales(request):
    from_date = request.GET.get('from')
    to_date = request.GET.get('to')
    today = timezone.now().date()

    if from_date:
        from_date = parse_date(from_date) or today - timedelta(days=30)
    else:
        from_date = today - timedelta(days=30)

    if to_date:
        to_date = parse_date(to_date) or today
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
    debtors = build_debtors_list(today)
    total_debt = sum(float(d['debt']) for d in debtors)

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
        order__completed_at__date__gte=start,
        order__completed_at__date__lte=end,
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


@login_required
def report_profit_loss(request):
    today = timezone.now().date()
    from_date, to_date, quick_days = resolve_profit_loss_dates(
        request.GET.get('from'),
        request.GET.get('to'),
        request.GET.get('quick_days'),
        today,
    )
    summary = compute_profit_loss(from_date, to_date)
    month_labels, month_revenue, month_expenses, month_profit = _monthly_financial_series(today, months=6)

    return render(request, 'blog/reports/profit_loss.html', {
        'from_date': from_date,
        'to_date': to_date,
        'quick_days': quick_days,
        'month_labels': month_labels,
        'month_revenue': month_revenue,
        'month_expenses': month_expenses,
        'month_profit': month_profit,
        **summary,
    })


