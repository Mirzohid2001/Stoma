from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.shortcuts import render

from ..models import ActivityLog
from ..utils import get_page_number


@staff_member_required
def activity_log(request):
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')
    paginator = Paginator(logs, 50)
    logs = paginator.get_page(get_page_number(request))
    return render(request, 'blog/activity_log.html', {'logs': logs})
