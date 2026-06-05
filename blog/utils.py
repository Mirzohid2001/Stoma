"""Blog ilovasi uchun yordamchi funksiyalar."""
from datetime import datetime, timedelta

from django.db.models import Case, Count, DecimalField, F, Q, Sum, Value, When
from django.db.models.functions import Coalesce

VALID_QUICK_DAYS = frozenset({7, 30, 90})
ELIGIBLE_DEBT_STATUSES = ('draft', 'in_progress', 'completed')


def get_page_number(request, param='page', default=1):
    """Request dan xavfsiz sahifa raqamini oladi (paginatsiya uchun)."""
    try:
        n = int(request.GET.get(param, default))
        return max(1, n)
    except (ValueError, TypeError):
        return default


def parse_date(s):
    """Satrni sanaga aylantiradi (YYYY-MM-DD). Bo'sh yoki noto'g'ri bo'lsa None."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def parse_quick_days(value):
    """Tez davr filtri (7/30/90 kun). Noto'g'ri qiymat bo'lsa None."""
    if value is None:
        return None
    try:
        days = int(value)
    except (TypeError, ValueError):
        return None
    if days in VALID_QUICK_DAYS:
        return days
    return None


def resolve_profit_loss_dates(from_str, to_str, quick_days_str, today):
    """Foyda/zarar hisoboti uchun from/to sanalarni aniqlaydi."""
    quick_days = parse_quick_days(quick_days_str)
    if quick_days:
        from_date = today - timedelta(days=quick_days - 1)
        return from_date, today, str(quick_days)

    from_date = parse_date(from_str)
    to_date = parse_date(to_str)
    if not from_date and not to_date:
        from_date = today.replace(day=1)
        to_date = today
    elif not from_date:
        from_date = today.replace(day=1)
    elif not to_date:
        to_date = today
    if from_date > to_date:
        from_date, to_date = to_date, from_date
    return from_date, to_date, None


def clients_with_stats(queryset=None):
    """Mijozlar querysetiga buyurtmalar, sarflangan va qarz statistikasini qo'shadi."""
    from .models import Client

    qs = queryset if queryset is not None else Client.objects.all()
    eligible = Q(orders__status__in=ELIGIBLE_DEBT_STATUSES)
    money_field = DecimalField(max_digits=14, decimal_places=2)
    zero = Value(0, output_field=money_field)

    return qs.annotate(
        stats_orders_count=Count('orders', distinct=True),
        stats_total_spent=Coalesce(Sum('orders__payments__amount'), zero, output_field=money_field),
        _eligible_price=Coalesce(
            Sum('orders__total_price', filter=eligible),
            zero,
            output_field=money_field,
        ),
        _eligible_paid=Coalesce(
            Sum('orders__payments__amount', filter=eligible),
            zero,
            output_field=money_field,
        ),
    ).annotate(
        stats_total_debt=Case(
            When(_eligible_price__gt=F('_eligible_paid'), then=F('_eligible_price') - F('_eligible_paid')),
            default=zero,
            output_field=money_field,
        ),
    )


def parse_calendar_month(year_str, month_str, today):
    """Kalendar uchun xavfsiz yil/oy qiymatlari."""
    try:
        year = int(year_str) if year_str else today.year
        month = int(month_str) if month_str else today.month
    except (TypeError, ValueError):
        return today.year, today.month
    if month < 1 or month > 12:
        month = today.month
    if year < 1 or year > 9999:
        year = today.year
    return year, month


def build_debtors_list(today):
    """Qarzdor mijozlar ro'yxati — eng yaqin to'lov sanasi bilan."""
    from .models import Order

    client_map = {}
    orders_qs = Order.objects.filter(
        status__in=['draft', 'in_progress', 'completed']
    ).select_related('client')

    for order in orders_qs:
        if order.remaining_debt <= 0:
            continue
        cid = order.client_id
        if cid not in client_map:
            client_map[cid] = {
                'client': order.client,
                'deadline': None,
            }
        dl = order.debt_payment_deadline
        if dl:
            current = client_map[cid]['deadline']
            if current is None or dl < current:
                client_map[cid]['deadline'] = dl

    debtors = []
    for data in client_map.values():
        dl = data['deadline']
        debtors.append({
            'client': data['client'],
            'debt': data['client'].total_debt,
            'deadline': dl,
            'days_left': (dl - today).days if dl else None,
        })

    debtors.sort(key=lambda x: (x['days_left'] if x['days_left'] is not None else 999, -float(x['debt'])))
    return debtors
