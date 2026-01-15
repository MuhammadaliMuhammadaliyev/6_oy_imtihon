from calendar import monthrange
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.template.defaulttags import comment
from django.utils.dateparse import parse_date
from unicodedata import category
from .models import Account, Category, Transaction
from .forms import AccountForm, CategoryForm, TransactionForm, CommentForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login


@login_required
def dashboard(request):
    q = request.GET.get("q", "")
    order = request.GET.get("order", "-date")
    start = request.GET.get("start", "")
    end = request.GET.get("end", "")

    transactions = Transaction.objects.filter(user=request.user).select_related("account", "category")
    if q:
        transactions = transactions.filter(Q(note__icontains=q) | Q(category__name__icontains=q))
    if start:
        transactions = transactions.filter(date__gte=start)
    if end:
        transactions = transactions.filter(date__lte=end)
    transactions = transactions.order_by(order)

    income_usd = sum(t.amount for t in transactions if t.type == "IN" and t.account.currency == "USD")
    expense_usd = sum(t.amount for t in transactions if t.type == "EX" and t.account.currency == "USD")
    balance_usd = income_usd - expense_usd

    income_uzs = sum(t.amount for t in transactions if t.type == "IN" and t.account.currency == "UZS")
    expense_uzs = sum(t.amount for t in transactions if t.type == "EX" and t.account.currency == "UZS")
    balance_uzs = income_uzs - expense_uzs

    return render(request, "dashboard.html", {
        "transactions": transactions,

        # USD
        "income_usd": income_usd,
        "expense_usd": expense_usd,
        "balance_usd": balance_usd,

        # UZS
        "income_uzs": income_uzs,
        "expense_uzs": expense_uzs,
        "balance_uzs": balance_uzs,

        "q": q,
        "order": order,
        "start": start,
        "end": end,
    })


@login_required
def transaction_create(request):
    form = TransactionForm(request.POST or None, user=request.user)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect('finance:dashboard')
    return render(request, 'transaction_form.html', {'form': form})


@login_required
def transaction_update(request, pk):
    transaction = Transaction.objects.filter(pk=pk, user=request.user).first()
    form = TransactionForm(request.POST or None, instance=transaction, user=request.user)
    if form.is_valid():
        form.save()
        return redirect('finance:dashboard')
    return render(request, 'transaction_form.html', {'form': form})


@login_required
def transaction_detail(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.transaction = transaction
        comment.user = request.user
        comment.save()
        return redirect('finance:detail', pk=pk)
    return render(request, 'transaction_detail.html', {'form':form, 'transaction':transaction})


@login_required
def transaction_delete(request, pk):
    forma = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        forma.delete()
        return redirect('finance:dashboard')
    return render(request, 'confirm_delete.html', {'forma':forma})


@login_required
def account_list(request):
    accounts = Account.objects.all().order_by('-id')
    return render(request, 'account_list.html', {'accounts':accounts})


@login_required
def account_create(request):
    form = AccountForm(request.POST or None)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect("finance:account_list")
    return render(request, "account_form.html", {"form": form})


@login_required
def account_update(request, pk):
    account = Account.objects.filter(pk=pk).first()
    form = AccountForm(request.POST or None, instance=account)
    if form.is_valid():
        form.save()
        return redirect('finance:account_list')
    return render(request, 'account_form.html', {'form': form})


@login_required
def account_delete(request, pk):
    account = Account.objects.filter(pk=pk).first()
    if request.method == 'POST':
        account.delete()
        return redirect('finance:account_list')
    return render(request, 'confirm_delete.html', {'account': account})


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).order_by('-id')
    return render(request, 'category_list.html', {'categories':categories})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        forma = form.save(commit=False)
        forma.user = request.user
        forma.save()
        return redirect('finance:category_list')
    return render(request, 'category_form.html', {'form':form})


@login_required
def category_update(request, pk):
    category = Category.objects.filter(pk=pk, user=request.user).first()
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('finance:category_list')
    return render(request, 'category_form.html', {'form':form})


@login_required
def category_delete(request, pk):
    category = Category.objects.filter(pk=pk, user=request.user).first()
    if request.method == 'POST':
        category.delete()
        return redirect('finance:category_list')
    return render(request, 'confirm_delete.html', {'category': category})


@login_required
def monthly_report(request):
    start = request.GET.get("start")
    end = request.GET.get("end")

    qs = Transaction.objects.filter(user=request.user)

    # agar sana tanlangan bo‘lsa filter qilamiz
    if start:
        qs = qs.filter(date__gte=parse_date(start))
    if end:
        qs = qs.filter(date__lte=parse_date(end))

    income = qs.filter(type="IN").aggregate(Sum("amount"))["amount__sum"] or 0
    expense = qs.filter(type="EX").aggregate(Sum("amount"))["amount__sum"] or 0
    balance = income - expense

    return render(request, "monthly_report.html", {
        "transactions": qs.order_by("-date"),
        "income": income,
        "expense": expense,
        "balance": balance,
        "start": start,
        "end": end,
    })




