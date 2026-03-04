import sys
from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'

    def ready(self):
        import blog.signals
        # Server ishlaganda bildirishnomalar har kuni avtomatik tekshiriladi
        if 'runserver' in sys.argv or 'gunicorn' in sys.argv[0]:
            from blog.notification_scheduler import start_notification_scheduler
            start_notification_scheduler()
