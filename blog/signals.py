from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import ActivityLog, Client, Order, Payment


def log_activity(user, action, model_name, obj=None, object_repr='', changes=None):
    if not user or not user.is_authenticated:
        return
    ActivityLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=obj.pk if obj else None,
        object_repr=(str(obj)[:200] if obj else object_repr),
        changes=changes or {}
    )


def _get_user():
    from .middleware import get_current_user
    return get_current_user()


@receiver(post_save, sender=Client)
def client_saved(sender, instance, created, **kwargs):
    if user := _get_user():
        log_activity(user, 'create' if created else 'update', 'Client', instance)


@receiver(post_save, sender=Order)
def order_saved(sender, instance, created, **kwargs):
    if user := _get_user():
        log_activity(user, 'create' if created else 'update', 'Order', instance)


@receiver(post_save, sender=Payment)
def payment_saved(sender, instance, created, **kwargs):
    if user := _get_user():
        log_activity(user, 'create' if created else 'update', 'Payment', instance)


@receiver(post_delete, sender=Client)
def client_deleted(sender, instance, **kwargs):
    if user := _get_user():
        log_activity(user, 'delete', 'Client', obj=instance)


@receiver(post_delete, sender=Order)
def order_deleted(sender, instance, **kwargs):
    if user := _get_user():
        log_activity(user, 'delete', 'Order', obj=instance)


@receiver(post_delete, sender=Payment)
def payment_deleted(sender, instance, **kwargs):
    if user := _get_user():
        log_activity(user, 'delete', 'Payment', obj=instance)
