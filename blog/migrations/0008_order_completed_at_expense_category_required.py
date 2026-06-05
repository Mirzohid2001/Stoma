from django.db import migrations, models
from django.utils import timezone


def backfill_completed_at(apps, schema_editor):
    Order = apps.get_model('blog', 'Order')
    for order in Order.objects.filter(status='completed', completed_at__isnull=True):
        order.completed_at = order.updated_at or timezone.now()
        order.save(update_fields=['completed_at'])


def assign_default_expense_category(apps, schema_editor):
    Expense = apps.get_model('blog', 'Expense')
    ExpenseCategory = apps.get_model('blog', 'ExpenseCategory')
    default = ExpenseCategory.objects.order_by('order', 'name').first()
    if default:
        Expense.objects.filter(category__isnull=True).update(category=default)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0007_expense_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='completed_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Tugallangan vaqt'),
        ),
        migrations.RunPython(backfill_completed_at, migrations.RunPython.noop),
        migrations.RunPython(assign_default_expense_category, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='expense',
            name='category',
            field=models.ForeignKey(
                on_delete=models.deletion.PROTECT,
                related_name='expenses',
                to='blog.expensecategory',
                verbose_name='Turi',
            ),
        ),
    ]
