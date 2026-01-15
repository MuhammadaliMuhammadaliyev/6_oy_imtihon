from django.db.models import DecimalField, Sum, When, F, Case   # ✅ Case shu yerda
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from finance.models import Account, Transaction
from .forms import RegisterForm, ProfileForm, ProfileEditForm



def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("finance:dashboard")  # finance dashboard
        else:
            messages.error(request, "Login yoki parol xato")
    return render(request, "users/login.html")


def user_logout(request):
    logout(request)
    return redirect("users:login")


def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('finance:dashboard')
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile(request):
    accounts = list(Account.objects.filter(user=request.user))
    tx = Transaction.objects.filter(user=request.user).select_related("account")

    # Har bir account uchun balansni hisoblab, account obyektiga qo‘shamiz
    for acc in accounts:
        income = sum(t.amount for t in tx if t.type == "IN" and t.account_id == acc.id)
        expense = sum(t.amount for t in tx if t.type == "EX" and t.account_id == acc.id)
        acc.calculated_balance = income - expense  # ✅ template’da ishlatamiz

    # USD umumiy
    income_usd = sum(t.amount for t in tx if t.type == "IN" and t.account.currency == "USD")
    expense_usd = sum(t.amount for t in tx if t.type == "EX" and t.account.currency == "USD")

    # UZS umumiy
    income_uzs = sum(t.amount for t in tx if t.type == "IN" and t.account.currency == "UZS")
    expense_uzs = sum(t.amount for t in tx if t.type == "EX" and t.account.currency == "UZS")

    totals = {
        "income_usd": income_usd,
        "expense_usd": expense_usd,
        "balance_usd": income_usd - expense_usd,
        "income_uzs": income_uzs,
        "expense_uzs": expense_uzs,
        "balance_uzs": income_uzs - expense_uzs,
    }

    return render(request, "users/profile.html", {
        "accounts": accounts,
        "totals": totals,
    })


@login_required
def profile_edit(request):
    form = ProfileEditForm(request.POST or None, instance=request.user)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Profil yangilandi ✅")
            return redirect("users:profile")

    return render(request, "users/profile_edit.html", {"form": form})