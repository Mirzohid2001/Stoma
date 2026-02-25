from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from ..forms import ClinicSettingsForm, NotificationSettingsForm
from ..models import ClinicSettings, NotificationSettings


@login_required
def settings_view(request):
    clinic = ClinicSettings.objects.first()
    if not clinic:
        clinic = ClinicSettings.objects.create()

    ns, _ = NotificationSettings.objects.get_or_create(
        user=request.user,
        defaults={'order_deadline_days': 3, 'debt_reminder_days': 5}
    )

    if request.method == 'POST':
        if 'clinic' in request.POST:
            form = ClinicSettingsForm(request.POST, instance=clinic)
            if form.is_valid():
                form.save()
                return redirect('settings')
        elif 'notifications' in request.POST:
            form = NotificationSettingsForm(request.POST, instance=ns)
            if form.is_valid():
                form.save()
                return redirect('settings')

    clinic_form = ClinicSettingsForm(instance=clinic)
    notif_form = NotificationSettingsForm(instance=ns)
    return render(request, 'blog/settings.html', {
        'clinic_form': clinic_form,
        'notif_form': notif_form,
    })
