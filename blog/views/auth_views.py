from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


def _safe_redirect_url(request, default='dashboard'):
    """Open redirect xavfsizligi: faqat relatif yo‘lga yo‘naltiradi."""
    next_url = request.GET.get('next', '').strip()
    if not next_url or next_url.startswith('//') or ':' in next_url.split('/', 1)[0]:
        return default
    if next_url.startswith('/') and not next_url.startswith('//'):
        return next_url
    return default


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(_safe_redirect_url(request))
        return render(request, 'blog/auth/login.html', {'error': True})
    return render(request, 'blog/auth/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('login')
