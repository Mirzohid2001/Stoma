from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from blog.tests.base import StomaTestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import Client, Expense, ExpenseCategory, Order, Payment, ServiceType


class ReportProfitLossViewTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')
        self.today = timezone.now().date()

        client_obj = Client.objects.create(full_name='Test Mijoz', phone='+998901111111')
        service = ServiceType.objects.create(name='Xizmat', default_price=50000)
        category = ExpenseCategory.objects.create(name='Ofis', order=1)
        order = Order.objects.create(
            client=client_obj,
            description='Test',
            service_type=service,
            total_price=Decimal('200000'),
            status='completed',
            created_by=self.user,
        )
        Payment.objects.create(
            order=order,
            amount=Decimal('200000'),
            payment_date=self.today,
            created_by=self.user,
        )
        Expense.objects.create(
            expense_date=self.today,
            amount=Decimal('50000'),
            category=category,
            created_by=self.user,
        )

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('report_profit_loss'))
        self.assertEqual(response.status_code, 302)

    def test_quick_days_7_filter(self):
        response = self.client.get(reverse('report_profit_loss'), {'quick_days': '7'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['quick_days'], '7')
        self.assertEqual(response.context['from_date'], self.today - timedelta(days=6))
        self.assertEqual(response.context['to_date'], self.today)
        self.assertContains(response, '7 kun')

    def test_quick_days_30_filter(self):
        response = self.client.get(reverse('report_profit_loss'), {'quick_days': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['quick_days'], '30')
        self.assertEqual(response.context['from_date'], self.today - timedelta(days=29))

    def test_manual_date_filter(self):
        response = self.client.get(reverse('report_profit_loss'), {
            'from': '2026-06-01',
            'to': '2026-06-05',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['quick_days'])
        self.assertEqual(response.context['from_date'], date(2026, 6, 1))
        self.assertEqual(response.context['to_date'], date(2026, 6, 5))

    def test_shows_profit_summary(self):
        response = self.client.get(reverse('report_profit_loss'), {'quick_days': '7'})
        self.assertEqual(float(response.context['revenue']), 200000.0)
        self.assertEqual(float(response.context['expense_amount']), 50000.0)


class ExportProfitLossViewTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')

    def test_excel_export_returns_xlsx(self):
        response = self.client.get(reverse('export_profit_loss_excel'), {'quick_days': '7'})
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            response['Content-Type'],
        )
        self.assertIn('foyda_zarar_', response['Content-Disposition'])

    def test_pdf_export_returns_pdf(self):
        response = self.client.get(reverse('export_profit_loss_pdf'), {'quick_days': '30'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('foyda_zarar_', response['Content-Disposition'])
