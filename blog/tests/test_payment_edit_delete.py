from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from blog.forms import PaymentForm
from blog.models import Client, Order, Payment, ServiceType
from blog.tests.base import StomaTestCase


class PaymentEditDeleteTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.order = Order.objects.create(
            client=self.client_obj,
            description='Test',
            service_type=self.service,
            total_price=Decimal('500000'),
            status='in_progress',
            created_by=self.user,
        )
        self.payment = Payment.objects.create(
            order=self.order,
            amount=Decimal('200000'),
            payment_date='2026-06-01',
            created_by=self.user,
        )

    def test_payment_form_allows_edit_within_total_limit(self):
        form = PaymentForm(
            {'amount': '300000', 'payment_date': '2026-06-02', 'payment_type': 'cash'},
            instance=self.payment,
            order=self.order,
        )
        self.assertTrue(form.is_valid())

    def test_payment_edit_view_updates_amount(self):
        response = self.client.post(reverse('payment_edit', args=[self.payment.pk]), {
            'amount': '250000',
            'payment_date': '2026-06-02',
            'payment_type': 'card',
        })
        self.assertEqual(response.status_code, 302)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.amount, Decimal('250000'))

    def test_payment_delete_view_removes_payment(self):
        response = self.client.post(reverse('payment_delete', args=[self.payment.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Payment.objects.filter(pk=self.payment.pk).exists())

    def test_payment_delete_from_list_redirects_to_list(self):
        response = self.client.post(reverse('payment_delete', args=[self.payment.pk]), {'next': 'payment_list'})
        self.assertRedirects(response, reverse('payment_list'))
