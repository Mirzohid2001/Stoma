import json

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ..models import NotificationSettings
from django.contrib.auth import get_user_model

User = get_user_model()


@csrf_exempt
@require_POST
def telegram_webhook(request):
    if not settings.TELEGRAM_BOT_TOKEN:
        return HttpResponse('ok')
    try:
        data = json.loads(request.body)
        message = data.get('message', {})
        text = message.get('text', '').strip()
        chat_id = str(message.get('chat', {}).get('id', ''))
        username = message.get('from', {}).get('username', '')

        if text == '/start' and chat_id:
            from_username = (message.get('from', {}).get('username') or '').strip().lower()
            ns = None
            if from_username:
                ns = NotificationSettings.objects.filter(
                    telegram_username__iexact=from_username
                ).first()
            if not ns:
                user = User.objects.filter(is_staff=True).first()
                if user:
                    ns, _ = NotificationSettings.objects.get_or_create(
                        user=user,
                        defaults={'order_deadline_days': 3, 'debt_reminder_days': 5}
                    )
            if ns:
                ns.telegram_chat_id = chat_id
                if from_username and not ns.telegram_username:
                    ns.telegram_username = from_username
                ns.save()
    except Exception:
        pass
    return HttpResponse('ok')
