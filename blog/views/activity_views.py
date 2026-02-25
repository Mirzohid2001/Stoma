from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from ..models import ActivityLog


@staff_member_required
def activity_log(request):
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(logs, 50)
    page = request.GET.get('page', 1)
    logs = paginator.get_page(page)
    return render(request, 'blog/activity_log.html', {'logs': logs})
