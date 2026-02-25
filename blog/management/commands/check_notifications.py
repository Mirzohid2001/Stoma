from django.core.management.base import BaseCommand
from blog.tasks import check_debt_reminders, check_order_deadlines


class Command(BaseCommand):
    help = 'Check deadlines and debts, create notifications'

    def handle(self, *args, **options):
        check_order_deadlines()
        check_debt_reminders()
        self.stdout.write(self.style.SUCCESS('Done'))
