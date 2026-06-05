from datetime import date

from django.test import SimpleTestCase

from blog.utils import parse_quick_days, resolve_profit_loss_dates


class ParseQuickDaysTests(SimpleTestCase):
    def test_valid_values(self):
        self.assertEqual(parse_quick_days('7'), 7)
        self.assertEqual(parse_quick_days('30'), 30)
        self.assertEqual(parse_quick_days('90'), 90)
        self.assertEqual(parse_quick_days(7), 7)

    def test_invalid_values(self):
        self.assertIsNone(parse_quick_days(None))
        self.assertIsNone(parse_quick_days(''))
        self.assertIsNone(parse_quick_days('14'))
        self.assertIsNone(parse_quick_days('abc'))


class ResolveProfitLossDatesTests(SimpleTestCase):
    def setUp(self):
        self.today = date(2026, 6, 5)

    def test_quick_days_7(self):
        from_date, to_date, quick = resolve_profit_loss_dates(None, None, '7', self.today)
        self.assertEqual(from_date, date(2026, 5, 30))
        self.assertEqual(to_date, self.today)
        self.assertEqual(quick, '7')

    def test_quick_days_30(self):
        from_date, to_date, quick = resolve_profit_loss_dates(None, None, '30', self.today)
        self.assertEqual(from_date, date(2026, 5, 7))
        self.assertEqual(to_date, self.today)
        self.assertEqual(quick, '30')

    def test_manual_dates(self):
        from_date, to_date, quick = resolve_profit_loss_dates('2026-06-01', '2026-06-03', None, self.today)
        self.assertEqual(from_date, date(2026, 6, 1))
        self.assertEqual(to_date, date(2026, 6, 3))
        self.assertIsNone(quick)

    def test_default_month_start(self):
        from_date, to_date, quick = resolve_profit_loss_dates(None, None, None, self.today)
        self.assertEqual(from_date, date(2026, 6, 1))
        self.assertEqual(to_date, self.today)
        self.assertIsNone(quick)

    def test_swaps_inverted_dates(self):
        from_date, to_date, _ = resolve_profit_loss_dates('2026-06-10', '2026-06-01', None, self.today)
        self.assertEqual(from_date, date(2026, 6, 1))
        self.assertEqual(to_date, date(2026, 6, 10))
