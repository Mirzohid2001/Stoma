from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from ..forms import ClinicSettingsForm, NotificationSettingsForm
from ..models import ClinicSettings, NotificationSettings


@login_required
@staff_member_required
def settings_view(request):
    clinic = ClinicSettings.objects.first()
    if not clinic:
        clinic = ClinicSettings.objects.create()

    ns, _ = NotificationSettings.objects.get_or_create(
        user=request.user,
        defaults={'order_deadline_days': 3, 'debt_reminder_days': 5}
    )

    clinic_form = ClinicSettingsForm(instance=clinic)
    notif_form = NotificationSettingsForm(instance=ns)

    if request.method == 'POST':
        if 'clinic' in request.POST:
            clinic_form = ClinicSettingsForm(request.POST, instance=clinic)
            if clinic_form.is_valid():
                clinic_form.save()
                messages.success(request, 'Klinika ma\'lumotlari saqlandi.')
                return redirect('settings')
        elif 'notifications' in request.POST:
            notif_form = NotificationSettingsForm(request.POST, instance=ns)
            if notif_form.is_valid():
                notif_form.save()
                messages.success(request, 'Bildirishnoma sozlamalari saqlandi.')
                return redirect('settings')

    return render(request, 'blog/settings.html', {
        'clinic_form': clinic_form,
        'notif_form': notif_form,
    })
