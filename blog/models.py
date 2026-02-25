from django.db import models
from django.conf import settings
from django.utils import timezone


class Client(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.full_name

    @property
    def total_spent(self):
        from django.db.models import Sum
        total = Payment.objects.filter(
            order__client=self
        ).aggregate(s=Sum('amount'))['s'] or 0
        return total

    @property
    def total_debt(self):
        total = 0
        for order in self.orders.filter(status__in=['draft', 'in_progress']):
            total += order.remaining_debt
        return total

    @property
    def orders_count(self):
        return self.orders.count()


class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    default_price = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Tugallangan'),
        ('cancelled', 'Bekor qilindi'),
    ]

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders')
    description = models.TextField()
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    total_price = models.DecimalField(max_digits=14, decimal_places=2)
    deadline = models.DateField(null=True, blank=True)
    debt_payment_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.client.full_name}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            from django.db.models import Max
            year = timezone.now().year
            last = Order.objects.filter(
                created_at__year=year
            ).aggregate(Max('order_number'))['order_number__max']
            if last and last.startswith(f'ORD-{year}-'):
                try:
                    num = int(last.split('-')[-1]) + 1
                except (ValueError, IndexError):
                    num = Order.objects.filter(created_at__year=year).count() + 1
            else:
                num = 1
            self.order_number = f"ORD-{year}-{num:04d}"
        super().save(*args, **kwargs)

    @property
    def paid_amount(self):
        from django.db.models import Sum
        total = self.payments.aggregate(s=Sum('amount'))['s'] or 0
        return total

    @property
    def remaining_debt(self):
        debt = self.total_price - self.paid_amount
        return max(debt, 0)

    @property
    def is_debtor(self):
        return self.remaining_debt > 0

    def mark_completed(self):
        self.status = 'completed'
        self.save(update_fields=['status', 'updated_at'])


class Payment(models.Model):
    PAYMENT_TYPES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('bank', 'Bank'),
        ('other', 'Boshqa'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField(default=timezone.now)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='cash')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_deadline', 'Zakaz deadline'),
        ('debt_reminder', 'Qarz eslatmasi'),
        ('system', 'Tizim'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    is_read = models.BooleanField(default=False)
    sent_to_telegram = models.BooleanField(default=False)
    related_order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    related_client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class NotificationSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    telegram_chat_id = models.CharField(max_length=50, blank=True)
    order_deadline_days = models.PositiveIntegerField(default=3)
    debt_reminder_days = models.PositiveIntegerField(default=5)
    notify_via_telegram = models.BooleanField(default=True)
    notify_in_system = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Yaratildi'),
        ('update', 'O\'zgartirildi'),
        ('delete', 'O\'chirildi'),
        ('complete', 'Tugallandi'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    changes = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name}"


class ClinicSettings(models.Model):
    clinic_name = models.CharField(max_length=200, default='Stomatologik klinika')
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    currency = models.CharField(max_length=10, default='UZS')

    class Meta:
        verbose_name_plural = 'Clinic settings'

    def __str__(self):
        return self.clinic_name
