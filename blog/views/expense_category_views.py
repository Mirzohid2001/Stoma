from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..forms import ExpenseCategoryForm
from ..models import ExpenseCategory
from ..utils import get_page_number


@login_required
def expense_category_list(request):
    items_qs = ExpenseCategory.objects.all().order_by('order', 'name')
    paginator = Paginator(items_qs, 20)
    items = paginator.get_page(get_page_number(request))
    return render(request, 'blog/expense_categories/list.html', {'items': items, 'page_obj': items})


@login_required
def expense_category_create(request):
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rasxod turi qo\'shildi.')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm()
    return render(request, 'blog/expense_categories/form.html', {'form': form, 'title': "Rasxod turini qo'shish"})


@login_required
def expense_category_edit(request, pk):
    item = get_object_or_404(ExpenseCategory, pk=pk)
    if request.method == 'POST':
        form = ExpenseCategoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Rasxod turi yangilandi.')
            return redirect('expense_category_list')
    else:
        form = ExpenseCategoryForm(instance=item)
    return render(request, 'blog/expense_categories/form.html', {'form': form, 'title': "Rasxod turini tahrirlash", 'item': item})


@login_required
@require_POST
def expense_category_delete(request, pk):
    item = get_object_or_404(ExpenseCategory, pk=pk)
    try:
        item.delete()
        messages.success(request, 'Rasxod turi o\'chirildi.')
    except ProtectedError:
        messages.error(request, 'Bu turga bog\'langan rasxodlar bor, o\'chirib bo\'lmadi.')
    return redirect('expense_category_list')
