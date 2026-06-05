from decimal import Decimal

from django.contrib.auth import get_user_model

from blog.forms import ExpenseForm
from blog.models import ExpenseCategory
from blog.tests.base import StomaTestCase


class ExpenseCategoryRequiredTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.category = ExpenseCategory.objects.create(name='Ofis', order=1)

    def test_expense_form_requires_category(self):
        form = ExpenseForm({
            'expense_date': '2026-06-05',
            'amount': '50000',
            'description': 'Test',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_expense_form_accepts_valid_category(self):
        form = ExpenseForm({
            'expense_date': '2026-06-05',
            'amount': '50000',
            'category': str(self.category.pk),
            'description': 'Test',
        })
        self.assertTrue(form.is_valid())
