import requests
from django.conf import settings
from django.utils import timezone

from .models import Notification, NotificationSettings, Order

try:
    from celery import shared_task
    @shared_task
    def run_notification_checks():
        check_order_deadlines()
        check_debt_reminders()
except ImportError:
    pass


def send_telegram(chat_id, text):
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': chat_id, 'text': text}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def check_order_deadlines():
    today = timezone.now().date()
    for ns in NotificationSettings.objects.filter(notify_in_system=True):
        from_date = today
        to_date = today + timezone.timedelta(days=ns.order_deadline_days)
        for order in Order.objects.filter(
            status__in=['draft', 'in_progress'],
            deadline__gte=from_date,
            deadline__lte=to_date
        ).select_related('client'):
            if Notification.objects.filter(
                user=ns.user,
                notification_type='order_deadline',
                related_order=order,
                created_at__date=today
            ).exists():
                continue
            msg = f"Zakaz {order.order_number} — {order.client.full_name}. Bitirishga {order.deadline} sanasiga {(order.deadline - today).days} kun qoldi."
            n = Notification.objects.create(
                user=ns.user,
                title="Deadline yaqinlashmoqda",
                message=msg,
                notification_type='order_deadline',
                related_order=order,
                related_client=order.client,
            )
            if ns.notify_via_telegram and ns.telegram_chat_id:
                if send_telegram(ns.telegram_chat_id, msg):
                    n.sent_to_telegram = True
                    n.save(update_fields=['sent_to_telegram'])


def check_debt_reminders():
    today = timezone.now().date()
    for ns in NotificationSettings.objects.filter(notify_in_system=True):
        to_date = today + timezone.timedelta(days=ns.debt_reminder_days)
        for order in Order.objects.filter(
            status__in=['draft', 'in_progress'],
            debt_payment_deadline__isnull=False
        ).filter(
            debt_payment_deadline__lte=to_date
        ).select_related('client'):
            if order.remaining_debt <= 0:
                continue
            if Notification.objects.filter(
                user=ns.user,
                notification_type='debt_reminder',
                related_order=order,
                created_at__date=today
            ).exists():
                continue
            days_left = (order.debt_payment_deadline - today).days
            if days_left < 0:
                days_text = f"{abs(days_left)} kun o'tgan"
            elif days_left == 0:
                days_text = "Bugun"
            else:
                days_text = f"To'lashga {days_left} kun qoldi"
            msg = f"Qarzdor: {order.client.full_name}. Qarz: {order.remaining_debt:,.0f} so'm. {days_text}."
            n = Notification.objects.create(
                user=ns.user,
                title="Qarz to'lovi yaqinlashmoqda",
                message=msg,
                notification_type='debt_reminder',
                related_order=order,
                related_client=order.client,
            )
            if ns.notify_via_telegram and ns.telegram_chat_id:
                if send_telegram(ns.telegram_chat_id, msg):
                    n.sent_to_telegram = True
                    n.save(update_fields=['sent_to_telegram'])
