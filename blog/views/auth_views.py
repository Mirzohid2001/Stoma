from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


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
            next_url = request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        return render(request, 'blog/auth/login.html', {'error': True})
    return render(request, 'blog/auth/login.html')


@require_http_methods(["GET", "POST"])
def logout_view(request):
    logout(request)
    return redirect('login')
