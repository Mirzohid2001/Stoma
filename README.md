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

**To‘liq qo‘llanma:** [docs/TELEGRAM_BOT.md](docs/TELEGRAM_BOT.md) — botni qanday yaratish, ulash va ishlatish.

Qisqacha:
1. @BotFather dan bot yarating, token oling
2. `.env` ga `TELEGRAM_BOT_TOKEN=...` va `PUBLIC_BASE_URL=https://SIZNING_DOMEN` qo'shing
3. Webhook o'rnating: `python manage.py set_telegram_webhook`
4. Botga /start yuboring — chat_id avtomatik saqlanadi (Sozlamalarda "Telegram orqali" ni yoqing)
5. **Qo‘shimcha buyruq kerak emas** — serverni ishga tushirganingizda (`runserver` yoki gunicorn) bildirishnomalar har kuni soat 9:00 da avtomatik tekshiriladi.

## Eslatma

- **Production** da `DEBUG=False` qiling va `ALLOWED_HOSTS` ni domeningizga o‘rnating.
- `createsuperuser` dan keyin default login yaratmasangiz, admin parolini tezda o‘zgartiring.
