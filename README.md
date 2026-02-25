# Stomatologik klinika boshqaruv tizimi

## O'rnatish

```bash
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
```

## Ishga tushirish

```bash
python manage.py runserver
```

Kirish: http://127.0.0.1:8000

Admin: http://127.0.0.1:8000/admin

## Telegram bildirishnomalar

1. @BotFather dan bot yarating
2. .env ga `TELEGRAM_BOT_TOKEN=...` qo'shing
3. Webhook o'rnating: `python manage.py set_telegram_webhook https://SIZNING_DOMEN/telegram/webhook/`
4. Botga /start yuboring — chat_id avtomatik saqlanadi
5. Celery va Redis ishga tushiring:

```bash
redis-server
celery -A config worker -l info
celery -A config beat -l info
```

Yoki `python manage.py check_notifications` ni cron orqali har kuni ishga tushiring.

## Default login

- username: admin
- parol: admin123 (o'zgartiring)
