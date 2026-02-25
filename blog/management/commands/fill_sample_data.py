from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from blog.models import Client, ClinicSettings, Notification, Order, Payment, ServiceType

User = get_user_model()


class Command(BaseCommand):
    help = 'Fill database with sample data'

    def handle(self, *args, **options):
        user = User.objects.filter(is_staff=True).first()
        if not user:
            user = User.objects.first()
        if not user:
            self.stderr.write('No user found. Create superuser first.')
            return

        today = timezone.now().date()

        ClinicSettings.objects.get_or_create(
            id=1,
            defaults={
                'clinic_name': 'DentArt Stomatologiya',
                'address': 'Toshkent, Amir Temur ko\'chasi 12',
                'phone': '+998 71 123 45 67',
                'currency': 'UZS',
            }
        )

        services = [
            ServiceType(name='Tish implantatsiyasi', default_price=5000000),
            ServiceType(name='Protez', default_price=1500000),
            ServiceType(name='Tozalash', default_price=200000),
            ServiceType(name='Kanal terapiyasi', default_price=800000),
            ServiceType(name='Oqartirish', default_price=600000),
        ]
        for s in services:
            ServiceType.objects.get_or_create(name=s.name, defaults={'default_price': s.default_price})

        clients_data = [
            ('Aziz Karimov', '+998901234567'),
            ('Nilufar Rahimova', '+998902345678'),
            ('Jasur Tursunov', '+998903456789'),
            ('Dilnoza Yusupova', '+998904567890'),
            ('Bobur Ismoilov', '+998905678901'),
            ('Malika Sodiqova', '+998906789012'),
            ('Sherzod Qodirov', '+998907890123'),
            ('Gulnora Azimova', '+998908901234'),
        ]

        clients = []
        for name, phone in clients_data:
            c, _ = Client.objects.get_or_create(phone=phone, defaults={'full_name': name, 'created_by': user})
            clients.append(c)

        Order.objects.all().delete()
        Payment.objects.all().delete()

        orders_data = [
            (clients[0], 'Tish implantatsiyasi — pastki o\'ng 6', 5500000, 5, 7),
            (clients[0], 'Protez — yuqori', 1800000, -3, 10),
            (clients[1], 'Tozalash + oqartirish', 750000, 2, 5),
            (clients[2], 'Kanal terapiyasi — 2 tish', 1600000, 4, 8),
            (clients[3], 'Protez — qisman', 1200000, 1, 6),
            (clients[4], 'Tish implantatsiyasi — yuqori o\'ng', 6000000, 10, 14),
            (clients[5], 'Tozalash', 250000, -1, 3),
            (clients[6], 'Kanal terapiyasi', 900000, 3, 7),
            (clients[7], 'Protez — to\'liq', 2500000, 7, 12),
        ]

        for client, desc, price, deadline_days, debt_days in orders_data:
            order = Order.objects.create(
                client=client,
                description=desc,
                total_price=price,
                deadline=today + timedelta(days=deadline_days),
                debt_payment_deadline=today + timedelta(days=debt_days),
                status='in_progress' if deadline_days > 0 else 'completed',
                created_by=user,
            )
            if price >= 2000000:
                Payment.objects.create(
                    order=order,
                    amount=price * 0.5,
                    payment_date=today - timedelta(days=2),
                    payment_type='cash',
                    created_by=user,
                )
            elif price >= 500000:
                Payment.objects.create(
                    order=order,
                    amount=price * 0.3,
                    payment_date=today - timedelta(days=1),
                    payment_type='card',
                    created_by=user,
                )

        Order.objects.create(
            client=clients[0],
            description='Tozalash',
            total_price=200000,
            deadline=today - timedelta(days=5),
            debt_payment_deadline=today - timedelta(days=2),
            status='completed',
            created_by=user,
        )

        Payment.objects.create(
            order=Order.objects.filter(client=clients[0], status='completed').first(),
            amount=200000,
            payment_date=today - timedelta(days=5),
            payment_type='cash',
            created_by=user,
        )

        Notification.objects.filter(user=user).delete()
        n1 = Order.objects.filter(status='in_progress', deadline__lte=today + timedelta(days=3)).first()
        if n1:
            Notification.objects.create(
                user=user,
                title='Deadline yaqinlashmoqda',
                message=f'Buyurtma {n1.order_number} — {n1.client.full_name}. Bitirishga {n1.deadline} sanasiga {(n1.deadline - today).days} kun qoldi.',
                notification_type='order_deadline',
                related_order=n1,
                related_client=n1.client,
            )
        debtor_order = None
        for o in Order.objects.filter(status='in_progress').select_related('client'):
            if o.remaining_debt > 0:
                debtor_order = o
                break
        if debtor_order:
            Notification.objects.create(
                user=user,
                title='Qarz eslatmasi',
                message=f'Qarzdor: {debtor_order.client.full_name}. Qarz: {debtor_order.remaining_debt:,.0f} so\'m.',
                notification_type='debt_reminder',
                related_order=debtor_order,
                related_client=debtor_order.client,
            )

        self.stdout.write(self.style.SUCCESS(
            f'Created: {Client.objects.count()} clients, {ServiceType.objects.count()} services, '
            f'{Order.objects.count()} orders, {Payment.objects.count()} payments'
        ))
