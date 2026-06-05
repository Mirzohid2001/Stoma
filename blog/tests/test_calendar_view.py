from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from blog.tests.base import StomaTestCase
from blog.utils import parse_calendar_month


class ParseCalendarMonthTests(StomaTestCase):
    def setUp(self):
        self.today = timezone.now().date()

    def test_invalid_year_uses_today(self):
        year, month = parse_calendar_month('abc', '6', self.today)
        self.assertEqual(year, self.today.year)
        self.assertEqual(month, 6)

    def test_invalid_month_uses_today_month(self):
        year, month = parse_calendar_month('2026', '99', self.today)
        self.assertEqual(year, 2026)
        self.assertEqual(month, self.today.month)


class CalendarViewTests(StomaTestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='pass')
        self.client.login(username='tester', password='pass')

    def test_invalid_year_does_not_500(self):
        response = self.client.get(reverse('calendar'), {'year': 'abc', 'month': '6'})
        self.assertEqual(response.status_code, 200)

    def test_invalid_month_does_not_500(self):
        response = self.client.get(reverse('calendar'), {'year': '2026', 'month': 'abc'})
        self.assertEqual(response.status_code, 200)
