from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from blog.models import Client, Order, OrderWorker, ServiceType, Worker
from blog.tests.base import StomaTestCase
from blog.views.report_views import compute_profit_loss


class CompletedAtTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.worker = Worker.objects.create(full_name='Doktor')

    def test_mark_completed_sets_completed_at(self):
        order = Order.objects.create(
            client=self.client_obj,
            description='Test',
            service_type=self.service,
            total_price=Decimal('1000000'),
            status='in_progress',
            created_by=self.user,
        )
        order.mark_completed()
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')
        self.assertIsNotNone(order.completed_at)

    def test_salary_uses_completed_at_not_created_at(self):
        old_date = timezone.now() - timedelta(days=40)
        order = Order.objects.create(
            client=self.client_obj,
            description='Eski buyurtma',
            service_type=self.service,
            total_price=Decimal('1000000'),
            status='completed',
            created_by=self.user,
        )
        Order.objects.filter(pk=order.pk).update(created_at=old_date)
        order.refresh_from_db()
        order.mark_completed()
        OrderWorker.objects.create(order=order, worker=self.worker, share_percent=Decimal('10'))

        today = timezone.now().date()
        month_start = today.replace(day=1)
        result = compute_profit_loss(month_start, today)
        self.assertEqual(result['salary'], 100000.0)

    def test_completed_before_period_excluded(self):
        order = Order.objects.create(
            client=self.client_obj,
            description='Test',
            service_type=self.service,
            total_price=Decimal('1000000'),
            status='completed',
            created_by=self.user,
        )
        past = timezone.now() - timedelta(days=60)
        Order.objects.filter(pk=order.pk).update(completed_at=past)
        OrderWorker.objects.create(order=order, worker=self.worker, share_percent=Decimal('10'))

        today = timezone.now().date()
        month_start = today.replace(day=1)
        result = compute_profit_loss(month_start, today)
        self.assertEqual(result['salary'], 0)
