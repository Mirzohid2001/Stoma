from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse

from blog.models import Client, Order, ServiceType, Worker
from blog.tests.base import StomaTestCase


class OrderCreateViewTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.worker = Worker.objects.create(full_name='Doktor')

    def _base_post_data(self):
        return {
            'client': str(self.client_obj.pk),
            'description': 'Test buyurtma',
            'service_type': str(self.service.pk),
            'quantity': '1',
            'total_price': '100000',
            'deadline': '',
            'debt_payment_deadline': '',
            'order_workers-TOTAL_FORMS': '1',
            'order_workers-INITIAL_FORMS': '0',
            'order_workers-MIN_NUM_FORMS': '0',
            'order_workers-MAX_NUM_FORMS': '15',
            'order_workers-0-id': '',
            'order_workers-0-order': '',
            'order_workers-0-DELETE': '',
        }

    def test_invalid_formset_does_not_create_order(self):
        data = self._base_post_data()
        data['order_workers-0-worker'] = str(self.worker.pk)
        data['order_workers-0-share_percent'] = '150'

        response = self.client.post(reverse('order_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertContains(response, 'Ulush 0 dan 100 gacha')

    def test_valid_form_and_formset_create_order(self):
        data = self._base_post_data()
        data['order_workers-0-worker'] = str(self.worker.pk)
        data['order_workers-0-share_percent'] = '50'

        response = self.client.post(reverse('order_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
