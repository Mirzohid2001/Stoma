import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.urls import reverse


class Command(BaseCommand):
    help = 'Set Telegram bot webhook URL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='Full webhook URL, e.g. https://example.com/telegram/webhook/. '
                 'If omitted, PUBLIC_BASE_URL + telegram_webhook path is used.'
        )

    def handle(self, *args, **options):
        token = settings.TELEGRAM_BOT_TOKEN
        if not token:
            self.stderr.write(self.style.ERROR('TELEGRAM_BOT_TOKEN not set'))
            return

        url = options.get('url')
        if not url:
            base = getattr(settings, 'PUBLIC_BASE_URL', '')
            if not base:
                self.stderr.write(
                    self.style.ERROR('PUBLIC_BASE_URL not set and --url not provided')
                )
                return
            path = reverse('telegram_webhook')
            url = base.rstrip('/') + path

        api_url = f'https://api.telegram.org/bot{token}/setWebhook'
        r = requests.post(api_url, json={'url': url}, timeout=10)
        if r.status_code == 200:
            self.stdout.write(self.style.SUCCESS(f'Webhook set to {url}'))
        else:
            self.stderr.write(self.style.ERROR(f'Failed: {r.text}'))
