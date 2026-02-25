from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from ..models import Notification


@login_required
def notification_count_api(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})


@login_required
def notification_list(request):
    qs = request.user.notifications.all()
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    notifications = paginator.get_page(page)
    return render(request, 'blog/notifications/list.html', {'notifications': notifications, 'page_obj': notifications})


@login_required
def notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    if notification.related_order_id:
        return redirect('order_detail', pk=notification.related_order_id)
    if notification.related_client_id:
        return redirect('client_detail', pk=notification.related_client_id)
    return redirect('notification_list')
