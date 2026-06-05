from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from blog.tests.base import StomaTestCase
from django.utils import timezone

from blog.models import Client, Expense, ExpenseCategory, Order, OrderWorker, Payment, ServiceType, Worker
from blog.views.report_views import compute_profit_loss


class ComputeProfitLossTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client_obj = Client.objects.create(full_name='Ali Valiyev', phone='+998901234567')
        self.service = ServiceType.objects.create(name='Plomba', default_price=100000)
        self.worker = Worker.objects.create(full_name='Doktor A')
        self.category = ExpenseCategory.objects.create(name='Ofis', order=1)
        self.period_start = date(2026, 6, 1)
        self.period_end = date(2026, 6, 5)

        self.order = Order.objects.create(
            client=self.client_obj,
            description='Test buyurtma',
            service_type=self.service,
            total_price=Decimal('1000000'),
            status='in_progress',
            created_by=self.user,
        )
        self.order.mark_completed()
        OrderWorker.objects.create(order=self.order, worker=self.worker, share_percent=Decimal('20'))

        Payment.objects.create(
            order=self.order,
            amount=Decimal('600000'),
            payment_date=date(2026, 6, 3),
            created_by=self.user,
        )
        Expense.objects.create(
            expense_date=date(2026, 6, 2),
            amount=Decimal('100000'),
            category=self.category,
            created_by=self.user,
        )

    def test_calculates_revenue_expenses_salary_and_profit(self):
        result = compute_profit_loss(self.period_start, self.period_end)

        self.assertEqual(float(result['revenue']), 600000.0)
        self.assertEqual(float(result['expense_amount']), 100000.0)
        self.assertEqual(result['salary'], 200000.0)
        self.assertEqual(result['total_expense'], 300000.0)
        self.assertEqual(result['net_profit'], 300000.0)
        self.assertAlmostEqual(result['margin'], 50.0)

    def test_zero_revenue_gives_zero_margin(self):
        Payment.objects.all().delete()
        result = compute_profit_loss(self.period_start, self.period_end)

        self.assertEqual(float(result['revenue']), 0.0)
        self.assertEqual(result['margin'], 0)

    def test_excludes_out_of_range_records(self):
        Payment.objects.create(
            order=self.order,
            amount=Decimal('500000'),
            payment_date=date(2026, 5, 20),
            created_by=self.user,
        )
        result = compute_profit_loss(self.period_start, self.period_end)
        self.assertEqual(float(result['revenue']), 600000.0)
