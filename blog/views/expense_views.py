from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..forms import ExpenseForm
from ..models import Expense
from ..utils import get_page_number, parse_date


@login_required
def expense_list(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    today = timezone.now().date()
    month_start = today.replace(day=1)

    from_date = parse_date(request.GET.get('from'))
    to_date = parse_date(request.GET.get('to'))
    if not from_date and not to_date:
        from_date = month_start
        to_date = today
    elif not from_date:
        from_date = month_start
    elif not to_date:
        to_date = today

    expenses_qs = Expense.objects.all().order_by('-expense_date')
    if from_date:
        expenses_qs = expenses_qs.filter(expense_date__gte=from_date)
    if to_date:
        expenses_qs = expenses_qs.filter(expense_date__lte=to_date)
    if q:
        expenses_qs = expenses_qs.filter(description__icontains=q)
    if category:
        expenses_qs = expenses_qs.filter(category=category)

    total = expenses_qs.aggregate(s=Sum('amount'))['s'] or 0
    by_category = list(
        expenses_qs.values('category')
        .annotate(s=Sum('amount'))
        .order_by('-s')
    )
    category_labels = dict(Expense.CATEGORY_CHOICES)
    by_category = [(category_labels.get(r['category'], r['category']), r['s']) for r in by_category]

    paginator = Paginator(expenses_qs, 20)
    expenses = paginator.get_page(get_page_number(request))

    return render(request, 'blog/expenses/list.html', {
        'expenses': expenses,
        'total': total,
        'by_category': by_category,
        'q': q,
        'category': category,
        'from_date': from_date,
        'to_date': to_date,
        'category_choices': Expense.CATEGORY_CHOICES,
    })


@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            messages.success(request, 'Rasxod qo\'shildi.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(initial={'expense_date': timezone.now().date()})
    return render(request, 'blog/expenses/form.html', {'form': form, 'title': 'Rasxod qo\'shish'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rasxod yangilandi.')
            return redirect('expense_list')
    else:
        form = ExpenseForm(instance=expense)
    return render(request, 'blog/expenses/form.html', {'form': form, 'title': 'Rasxodni tahrirlash', 'expense': expense})


@login_required
@require_POST
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, 'Rasxod o\'chirildi.')
    return redirect('expense_list')
