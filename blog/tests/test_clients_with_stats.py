from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from blog.models import Client, Order, Payment, ServiceType
from blog.tests.base import StomaTestCase
from blog.utils import clients_with_stats


class ClientsWithStatsTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.client_a = Client.objects.create(full_name='Ali', phone='+998901111111')
        self.client_b = Client.objects.create(full_name='Vali', phone='+998902222222')

        order_a = Order.objects.create(
            client=self.client_a,
            description='A1',
            service_type=self.service,
            total_price=Decimal('300000'),
            status='in_progress',
            created_by=self.user,
        )
        Order.objects.create(
            client=self.client_a,
            description='A2',
            service_type=self.service,
            total_price=Decimal('200000'),
            status='completed',
            created_by=self.user,
        )
        Payment.objects.create(order=order_a, amount=Decimal('100000'), created_by=self.user)

    def test_annotates_orders_spent_and_debt(self):
        client = clients_with_stats(Client.objects.filter(pk=self.client_a.pk)).get()
        self.assertEqual(client.stats_orders_count, 2)
        self.assertEqual(float(client.stats_total_spent), 100000.0)
        self.assertEqual(float(client.stats_total_debt), 400000.0)

    def test_client_list_uses_single_query_for_page(self):
        self.client.login(username='tester', password='pass')
        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(reverse('client_list'))
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(ctx.captured_queries), 6)
