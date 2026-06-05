from decimal import Decimal

from django.contrib.auth import get_user_model

from blog.forms import PaymentForm
from blog.models import Client, Order, Payment, ServiceType
from blog.tests.base import StomaTestCase


class PaymentFormTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.order = Order.objects.create(
            client=self.client_obj,
            description='Test',
            service_type=self.service,
            total_price=Decimal('500000'),
            status='completed',
            created_by=self.user,
        )
        Payment.objects.create(
            order=self.order,
            amount=Decimal('500000'),
            created_by=self.user,
        )

    def test_rejects_payment_when_debt_is_zero(self):
        form = PaymentForm({'amount': '1000', 'payment_date': '2026-06-05', 'payment_type': 'cash'}, order=self.order)
        self.assertFalse(form.is_valid())
        self.assertIn('amount', form.errors)

    def test_allows_payment_up_to_remaining_debt(self):
        Payment.objects.all().delete()
        Payment.objects.create(order=self.order, amount=Decimal('300000'), created_by=self.user)
        form = PaymentForm({'amount': '200000', 'payment_date': '2026-06-05', 'payment_type': 'cash'}, order=self.order)
        self.assertTrue(form.is_valid())

    def test_rejects_overpayment(self):
        Payment.objects.all().delete()
        Payment.objects.create(order=self.order, amount=Decimal('300000'), created_by=self.user)
        form = PaymentForm({'amount': '250000', 'payment_date': '2026-06-05', 'payment_type': 'cash'}, order=self.order)
        self.assertFalse(form.is_valid())
