from decimal import Decimal

from django.db.models import DecimalField, Sum
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from finance.models import Account, Transaction, ExchangeRate
from .forms import RegisterForm, ProfileEditForm


def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("finance:dashboard")
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
        return redirect("finance:dashboard")
    return render(request, "users/register.html", {"form": form})


# ✅ Professional SUM helper (DecimalField xatosiz)
def _sum_amount(qs):
    return qs.aggregate(
        s=Coalesce(
            Sum("amount"),
            Decimal("0"),
            output_field=DecimalField(max_digits=15, decimal_places=2),
        )
    )["s"]


def _get_usd_rate():
    # eng oxirgi kurs: 1 USD = rate UZS
    obj = ExchangeRate.objects.filter(base="USD", quote="UZS").order_by("-date").first()
    return obj.rate if obj else Decimal("0")


@login_required
def profile(request):
    accounts = list(Account.objects.filter(user=request.user).order_by("-id"))
    tx = Transaction.objects.filter(user=request.user).select_related("account")

    # ✅ har bir account uchun balans (ORM)
    for acc in accounts:
        inc = _sum_amount(tx.filter(type="IN", account=acc))
        exp = _sum_amount(tx.filter(type="EX", account=acc))
        acc.calculated_balance = inc - exp  # template’da ishlatamiz

    # ✅ USD totals (ORM)
    income_usd = _sum_amount(tx.filter(type="IN", account__currency="USD"))
    expense_usd = _sum_amount(tx.filter(type="EX", account__currency="USD"))
    balance_usd = income_usd - expense_usd

    # ✅ UZS totals (ORM)
    income_uzs = _sum_amount(tx.filter(type="IN", account__currency="UZS"))
    expense_uzs = _sum_amount(tx.filter(type="EX", account__currency="UZS"))
    balance_uzs = income_uzs - expense_uzs

    # ✅ TOTAL (UZS) kurs bilan
    usd_rate = _get_usd_rate()
    total_balance_uzs = balance_uzs + (balance_usd * usd_rate)

    totals = {
        "income_usd": income_usd,
        "expense_usd": expense_usd,
        "balance_usd": balance_usd,

        "income_uzs": income_uzs,
        "expense_uzs": expense_uzs,
        "balance_uzs": balance_uzs,

        # TOTAL
        "usd_rate": usd_rate,
        "total_balance_uzs": total_balance_uzs,
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
