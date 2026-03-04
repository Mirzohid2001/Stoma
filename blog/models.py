from django.db import models
from django.conf import settings
from django.utils import timezone


class Client(models.Model):
    full_name = models.CharField('To\'liq ism', max_length=200)
    phone = models.CharField('Telefon', max_length=20)
    notes = models.TextField('Eslatmalar', blank=True)
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
        verbose_name = 'Mijoz'
        verbose_name_plural = 'Mijozlar'

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
        for order in self.orders.all():
            if order.status in ('draft', 'in_progress', 'completed'):
                total += order.remaining_debt
        return total

    @property
    def orders_count(self):
        return self.orders.count()


class ServiceType(models.Model):
    name = models.CharField('Nomi', max_length=100)
    default_price = models.DecimalField('Standart narx', max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Xizmat turi'
        verbose_name_plural = 'Xizmat turlari'

    def __str__(self):
        return self.name


class Worker(models.Model):
    """Ishchi — buyurtmada ishlaydigan xodim, oylik ish haqi buyurtma ulushiga qarab hisoblanadi."""
    full_name = models.CharField('To\'liq ism', max_length=200)
    phone = models.CharField('Telefon', max_length=20, blank=True)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = 'Ishchi'
        verbose_name_plural = 'Ishchilar'

    def __str__(self):
        return self.full_name


class Order(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('in_progress', 'Jarayonda'),
        ('completed', 'Tugallangan'),
        ('cancelled', 'Bekor qilindi'),
    ]

    order_number = models.CharField('Buyurtma raqami', max_length=20, unique=True, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='orders', verbose_name='Mijoz')
    description = models.TextField('Tavsif')
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Xizmat turi'
    )
    quantity = models.PositiveIntegerField('Miqdori', default=1)
    total_price = models.DecimalField('Umumiy summa', max_digits=14, decimal_places=2)
    deadline = models.DateField('Tayyor bo\'lish sanasi', null=True, blank=True)
    debt_payment_deadline = models.DateField('Qarz to\'lov sanasi', null=True, blank=True)
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='draft')
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
        verbose_name = 'Buyurtma'
        verbose_name_plural = 'Buyurtmalar'

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

    def mark_cancelled(self):
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])


class OrderWorker(models.Model):
    """Buyurtmada qatnashgan ishchi va uning ulush foizi (ish haqi ishbay)."""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_workers', verbose_name='Buyurtma')
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE, related_name='order_workers', verbose_name='Ishchi')
    share_percent = models.DecimalField(
        'Ulush (%)',
        max_digits=5,
        decimal_places=2,
        default=100,
        help_text='Buyurtma summasidan ushbu ishchiga tegishli foiz (0–100)'
    )

    class Meta:
        unique_together = [('order', 'worker')]
        verbose_name = 'Buyurtmadagi ishchi'
        verbose_name_plural = 'Buyurtmadagi ishchilar'

    def __str__(self):
        return f"{self.order.order_number} — {self.worker.full_name} ({self.share_percent}%)"


class Payment(models.Model):
    PAYMENT_TYPES = [
        ('cash', 'Naqd'),
        ('card', 'Karta'),
        ('bank', 'Bank'),
        ('other', 'Boshqa'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name='Buyurtma')
    amount = models.DecimalField('Summa', max_digits=14, decimal_places=2)
    payment_date = models.DateField('To\'lov sanasi', default=timezone.now)
    payment_type = models.CharField('To\'lov turi', max_length=20, choices=PAYMENT_TYPES, default='cash')
    notes = models.TextField('Eslatma', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-payment_date', '-created_at']
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'

    def __str__(self):
        return f"{self.order.order_number} - {self.amount}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_deadline', 'Zakaz muddati'),
        ('debt_reminder', 'Qarz eslatmasi'),
        ('system', 'Tizim'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField('Sarlavha', max_length=200)
    message = models.TextField('Xabar')
    notification_type = models.CharField(
        'Turi',
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    is_read = models.BooleanField('O\'qilgan', default=False)
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
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'

    def __str__(self):
        return self.title


class NotificationSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_settings'
    )
    telegram_chat_id = models.CharField('Telegram chat ID', max_length=50, blank=True)
    telegram_username = models.CharField(
        'Telegram username',
        max_length=64,
        blank=True,
        help_text='Botga /start yuborishdan oldin @ siz Telegram username ni shu yerga yozing (masalan: john_doe)'
    )
    order_deadline_days = models.PositiveIntegerField('Zakaz muddati (kun)', default=3)
    debt_reminder_days = models.PositiveIntegerField('Qarz eslatmasi (kun)', default=5)
    notify_via_telegram = models.BooleanField('Telegram orqali', default=True)
    notify_in_system = models.BooleanField('Tizimda', default=True)

    class Meta:
        verbose_name = 'Bildirishnoma sozlamalari'
        verbose_name_plural = 'Bildirishnoma sozlamalari'

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
        verbose_name = 'Harakatlar jurnali'
        verbose_name_plural = 'Harakatlar jurnali'

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name}"


class Expense(models.Model):
    """Rasxod (klinika chiqimlari)."""
    CATEGORY_CHOICES = [
        ('office', 'Ofis'),
        ('salary', 'Maosh'),
        ('equipment', 'Jihoz / uskuna'),
        ('utilities', 'Kommunal'),
        ('medication', 'Dori-darmon'),
        ('other', 'Boshqa'),
    ]
    expense_date = models.DateField('Sana', default=timezone.now)
    amount = models.DecimalField('Summa', max_digits=14, decimal_places=2)
    category = models.CharField('Turi', max_length=20, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField('Tavsif', max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['-expense_date', '-created_at']
        verbose_name = 'Rasxod'
        verbose_name_plural = 'Rasxodlar'

    def __str__(self):
        return f"{self.expense_date} — {self.get_category_display()} ({self.amount:,.0f} so'm)"


class ClinicSettings(models.Model):
    clinic_name = models.CharField('Klinika nomi', max_length=200, default='Stomatologik klinika')
    address = models.TextField('Manzil', blank=True)
    phone = models.CharField('Telefon', max_length=50, blank=True)
    currency = models.CharField('Valyuta', max_length=10, default='UZS')

    class Meta:
        verbose_name = 'Klinika sozlamalari'
        verbose_name_plural = 'Klinika sozlamalari'

    def __str__(self):
        return self.clinic_name
