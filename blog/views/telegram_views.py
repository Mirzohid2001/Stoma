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
            user = User.objects.filter(is_staff=True).first()
            if user:
                ns, _ = NotificationSettings.objects.get_or_create(
                    user=user,
                    defaults={'order_deadline_days': 3, 'debt_reminder_days': 5}
                )
                ns.telegram_chat_id = chat_id
                ns.save()
    except Exception:
        pass
    return HttpResponse('ok')
