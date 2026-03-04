"""
Django ishga tushganda bildirishnomalar tekshiruvi har kuni avtomatik ishlaydi.
Qo'shimcha buyruq (check_notifications) yoki Celery talab qilinmaydi.
"""
import logging
import threading
import time

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Har kuni soat 9:00 da (Toshkent vaqti) tekshiruv
NOTIFICATION_HOUR = 9
NOTIFICATION_MINUTE = 0


def _seconds_until_next_run():
    """Keyingi kun soat 9:00 gacha necha sekund qolganini hisoblaydi."""
    tz = timezone.get_current_timezone()
    now = timezone.now().astimezone(tz)
    next_run = now.replace(hour=NOTIFICATION_HOUR, minute=NOTIFICATION_MINUTE, second=0, microsecond=0)
    if next_run <= now:
        next_run += timezone.timedelta(days=1)
    return (next_run - now).total_seconds()


def _run_checks():
    """Zakaz muddati va qarz eslatmalarini tekshiradi."""
    from django.db import close_old_connections
    try:
        close_old_connections()
        from blog.tasks import check_order_deadlines, check_debt_reminders
        check_order_deadlines()
        check_debt_reminders()
        logger.info('Bildirishnomalar tekshiruvi bajarildi')
    except Exception as e:
        logger.exception('Bildirishnomalar tekshiruvida xato: %s', e)
    finally:
        close_old_connections()


def _scheduler_loop():
    """Har kuni bir marta (9:00 da) tekshiruvni ishga tushiradi."""
    # Birinchi marta 1 daqiqa kutib, keyin har 24 soatda
    time.sleep(60)
    while True:
        try:
            _run_checks()
        except Exception:
            logger.exception('Scheduler xato')
        # Keyingi kun 9:00 gacha uxlash
        time.sleep(_seconds_until_next_run())


def start_notification_scheduler():
    """Fon daemon thread da reja ishga tushiradi."""
    if getattr(settings, 'NOTIFICATION_SCHEDULER_DISABLED', False):
        return
    thread = threading.Thread(target=_scheduler_loop, daemon=True, name='notification-scheduler')
    thread.start()
    logger.info('Bildirishnomalar rejasi ishga tushdi (har kuni soat 9:00)')
