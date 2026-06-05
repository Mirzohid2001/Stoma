from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model

from blog.models import Client, Order, Payment, ServiceType
from blog.tests.base import StomaTestCase
from blog.utils import build_debtors_list


class BuildDebtorsListTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.today = date(2026, 6, 5)

    def test_uses_earliest_deadline_among_debt_orders(self):
        Order.objects.create(
            client=self.client_obj,
            description='Buyurtma 1',
            service_type=self.service,
            total_price=Decimal('300000'),
            debt_payment_deadline=date(2026, 6, 20),
            status='in_progress',
            created_by=self.user,
        )
        Order.objects.create(
            client=self.client_obj,
            description='Buyurtma 2',
            service_type=self.service,
            total_price=Decimal('200000'),
            debt_payment_deadline=date(2026, 6, 10),
            status='in_progress',
            created_by=self.user,
        )

        debtors = build_debtors_list(self.today)
        self.assertEqual(len(debtors), 1)
        self.assertEqual(debtors[0]['deadline'], date(2026, 6, 10))
        self.assertEqual(float(debtors[0]['debt']), 500000.0)
        self.assertEqual(debtors[0]['days_left'], 5)

    def test_excludes_fully_paid_clients(self):
        order = Order.objects.create(
            client=self.client_obj,
            description='To\'langan',
            service_type=self.service,
            total_price=Decimal('100000'),
            status='completed',
            created_by=self.user,
        )
        Payment.objects.create(
            order=order,
            amount=Decimal('100000'),
            payment_date=self.today,
            created_by=self.user,
        )
        debtors = build_debtors_list(self.today)
        self.assertEqual(debtors, [])
