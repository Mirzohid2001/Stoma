from django.contrib import admin
from .models import Client, ClinicSettings, Notification, NotificationSettings, Order, Payment, ServiceType


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'created_at']
    search_fields = ['full_name', 'phone']


@admin.register(ServiceType)
class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_price']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'client', 'total_price', 'status', 'deadline']
    list_filter = ['status']
    search_fields = ['order_number', 'client__full_name']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'amount', 'payment_date', 'payment_type']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'order_deadline_days', 'debt_reminder_days']


@admin.register(ClinicSettings)
class ClinicSettingsAdmin(admin.ModelAdmin):
    list_display = ['clinic_name', 'phone']
