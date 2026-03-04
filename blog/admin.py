from django.contrib import admin
from django.utils.html import format_html
from .models import (
    ActivityLog,
    Client,
    ClinicSettings,
    Expense,
    Notification,
    NotificationSettings,
    Order,
    OrderWorker,
    Payment,
    ServiceType,
    Worker,
)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'orders_count', 'created_at']
    list_display_links = ['full_name']
    search_fields = ['full_name', 'phone', 'notes']
    list_filter = ['created_at']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    list_per_page = 25
    ordering = ['-created_at']


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_price']
    list_editable = ['default_price']
    search_fields = ['name']


class OrderWorkerInline(admin.TabularInline):
    model = OrderWorker
    extra = 1
    autocomplete_fields = ['worker']
    verbose_name = 'Buyurtmadagi ishchi'
    verbose_name_plural = 'Buyurtmadagi ishchilar'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'client',
        'service_type',
        'total_price',
        'paid_display',
        'debt_display',
        'status',
        'deadline',
        'created_at',
    ]
    list_display_links = ['order_number']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    search_fields = ['order_number', 'client__full_name', 'client__phone', 'description']
    date_hierarchy = 'created_at'
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    autocomplete_fields = ['client', 'service_type']
    inlines = [OrderWorkerInline]
    list_per_page = 25
    ordering = ['-created_at']

    def paid_display(self, obj):
        return format_html('{} so\'m', f'{obj.paid_amount:,.0f}')
    paid_display.short_description = "To'langan"

    def debt_display(self, obj):
        debt = obj.remaining_debt
        if debt > 0:
            return format_html('<span style="color: red;">{} so\'m</span>', f'{debt:,.0f}')
        return format_html('{} so\'m', '0')
    debt_display.short_description = 'Qoldiq'


@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'is_active', 'order_workers_count']
    list_display_links = ['full_name']
    list_filter = ['is_active']
    list_editable = ['is_active']
    search_fields = ['full_name', 'phone']
    list_per_page = 25

    def order_workers_count(self, obj):
        return obj.order_workers.count()
    order_workers_count.short_description = 'Buyurtmalar (ishbay)'


@admin.register(OrderWorker)
class OrderWorkerAdmin(admin.ModelAdmin):
    list_display = ['order', 'worker', 'share_percent', 'amount_display']
    list_filter = ['worker']
    search_fields = ['order__order_number', 'worker__full_name']
    autocomplete_fields = ['order', 'worker']
    list_select_related = ['order', 'worker']
    list_per_page = 25

    def amount_display(self, obj):
        amount = float(obj.order.total_price) * float(obj.share_percent) / 100
        return format_html('{} so\'m', f'{amount:,.0f}')
    amount_display.short_description = 'Summa (ish haqi)'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_type', 'payment_date', 'created_at']
    list_display_links = ['order']
    list_filter = ['payment_type', 'payment_date']
    date_hierarchy = 'payment_date'
    search_fields = ['order__order_number', 'order__client__full_name']
    autocomplete_fields = ['order']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-payment_date', '-created_at']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['is_read', 'notification_type']
    date_hierarchy = 'created_at'
    search_fields = ['title', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-created_at']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_deadline_days', 'debt_reminder_days', 'notify_via_telegram', 'notify_in_system']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['expense_date', 'category', 'amount', 'description', 'created_at']
    list_filter = ['category', 'expense_date']
    date_hierarchy = 'expense_date'
    search_fields = ['description']
    readonly_fields = ['created_at']
    list_per_page = 25
    ordering = ['-expense_date', '-created_at']


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ['clinic_name', 'phone', 'currency']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'model_name', 'object_repr', 'created_at']
    list_filter = ['action', 'model_name', 'created_at']
    date_hierarchy = 'created_at'
    search_fields = ['user__username', 'object_repr']
    readonly_fields = ['user', 'action', 'model_name', 'object_id', 'object_repr', 'changes', 'created_at']
    list_per_page = 50
    ordering = ['-created_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
