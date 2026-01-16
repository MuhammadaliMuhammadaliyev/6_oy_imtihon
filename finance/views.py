from calendar import monthrange
from datetime import date
from decimal import Decimal
from django.db import transaction as db_transaction
from django.db.models.functions import TruncMonth, Coalesce
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from .models import Account, Category, Transaction
from .forms import AccountForm, CategoryForm, TransactionForm, CommentForm, TransferForm
from .services.exchange import convert


# ========= Helpers (Professional totals) =========
def _sum_amount(qs):
    return qs.aggregate(s=Coalesce(Sum("amount"), Decimal("0")))["s"]


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

    # ==== UZS hisob ====
    income_uzs = _sum_amount(transactions.filter(type="IN", account__currency="UZS"))
    expense_uzs = _sum_amount(transactions.filter(type="EX", account__currency="UZS"))
    balance_uzs = income_uzs - expense_uzs

    # ==== USD hisob ====
    income_usd = _sum_amount(transactions.filter(type="IN", account__currency="USD"))
    expense_usd = _sum_amount(transactions.filter(type="EX", account__currency="USD"))
    balance_usd = income_usd - expense_usd

    # ==== ✅ Umumiy balans (bitta valyutada) ====
    # USD balansni UZS ga avtomatik konvert qilamiz
    try:
        usd_to_uzs = convert(balance_usd, "USD", "UZS")
    except Exception:
        usd_to_uzs = 0   # agar kurs kiritilmagan bo‘lsa yiqilmasin

    total_balance_uzs = balance_uzs + usd_to_uzs

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

        # ✅ Umumiy
        "total_balance_uzs": total_balance_uzs,

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

    return render(request, 'transaction_detail.html', {'form': form, 'transaction': transaction})


@login_required
def transaction_delete(request, pk):
    forma = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        forma.delete()
        return redirect('finance:dashboard')
    return render(request, 'confirm_delete.html', {'forma': forma})


@login_required
def account_list(request):
    # ✅ SECURITY: faqat o'zingizniki
    accounts = Account.objects.filter(user=request.user).order_by('-id')
    return render(request, 'account_list.html', {'accounts': accounts})


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
    account = Account.objects.filter(pk=pk, user=request.user).first()
    form = AccountForm(request.POST or None, instance=account)
    if form.is_valid():
        form.save()
        return redirect('finance:account_list')
    return render(request, 'account_form.html', {'form': form})


@login_required
def account_delete(request, pk):
    account = Account.objects.filter(pk=pk, user=request.user).first()
    if request.method == 'POST':
        account.delete()
        return redirect('finance:account_list')
    return render(request, 'confirm_delete.html', {'account': account})


@login_required
def category_list(request):
    categories = Category.objects.filter(user=request.user).order_by('-id')
    return render(request, 'category_list.html', {'categories': categories})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if form.is_valid():
        forma = form.save(commit=False)
        forma.user = request.user
        forma.save()
        return redirect('finance:category_list')
    return render(request, 'category_form.html', {'form': form})


@login_required
def category_update(request, pk):
    category = Category.objects.filter(pk=pk, user=request.user).first()
    form = CategoryForm(request.POST or None, instance=category)
    if form.is_valid():
        form.save()
        return redirect('finance:category_list')
    return render(request, 'category_form.html', {'form': form})


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

    qs = Transaction.objects.filter(user=request.user).select_related("account")

    if start:
        qs = qs.filter(date__gte=parse_date(start))
    if end:
        qs = qs.filter(date__lte=parse_date(end))

    # ✅ Professional: USD/UZS alohida
    income_uzs = _sum_amount(qs.filter(type="IN", account__currency="UZS"))
    expense_uzs = _sum_amount(qs.filter(type="EX", account__currency="UZS"))
    balance_uzs = income_uzs - expense_uzs

    income_usd = _sum_amount(qs.filter(type="IN", account__currency="USD"))
    expense_usd = _sum_amount(qs.filter(type="EX", account__currency="USD"))
    balance_usd = income_usd - expense_usd

    return render(request, "monthly_report.html", {
        "transactions": qs.order_by("-date"),

        # UZS
        "income_uzs": income_uzs,
        "expense_uzs": expense_uzs,
        "balance_uzs": balance_uzs,

        # USD
        "income_usd": income_usd,
        "expense_usd": expense_usd,
        "balance_usd": balance_usd,

        "start": start,
        "end": end,
    })


@login_required
def transfer_create(request):
    form = TransferForm(request.POST or None, user=request.user)
    if form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.full_clean()

        with db_transaction.atomic():
            obj.save()

            cat_out, _ = Category.objects.get_or_create(
                user=request.user, type="EX", name="Transfer (chiqim)"
            )
            cat_in, _ = Category.objects.get_or_create(
                user=request.user, type="IN", name="Transfer (kirim)"
            )

            out_tx = Transaction.objects.create(
                user=request.user,
                type="EX",
                category=cat_out,
                account=obj.from_account,
                amount=obj.amount_from,
                date=obj.date,
                note=(obj.note or "")[:200],
            )

            in_amount = obj.amount_to if obj.amount_to is not None else obj.amount_from
            in_tx = Transaction.objects.create(
                user=request.user,
                type="IN",
                category=cat_in,
                account=obj.to_account,
                amount=in_amount,
                date=obj.date,
                note=(obj.note or "")[:200],
            )

            obj.out_tx = out_tx
            obj.in_tx = in_tx
            obj.save(update_fields=["out_tx", "in_tx"])

        return redirect("finance:dashboard")

    return render(request, "transfer_form.html", {"form": form})


@login_required
def analytics(request):
    year = int(request.GET.get("year", date.today().year))
    currency = request.GET.get("currency", "UZS")

    base = (
        Transaction.objects
        .filter(user=request.user, date__year=year, account__currency=currency)
        .annotate(m=TruncMonth("date"))
        .values("m", "type")
        .annotate(total=Sum("amount"))
        .order_by("m")
    )

    bucket = {}
    for r in base:
        m = r["m"].strftime("%Y-%m")
        bucket.setdefault(m, {"IN": 0, "EX": 0})
        bucket[m][r["type"]] = float(r["total"] or 0)

    labels = sorted(bucket.keys())
    income = [bucket[m]["IN"] for m in labels]
    expense = [bucket[m]["EX"] for m in labels]

    cat_qs = (
        Transaction.objects
        .filter(user=request.user, type="EX", date__year=year, account__currency=currency)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")[:10]
    )

    cat_labels = [x["category__name"] for x in cat_qs]
    cat_values = [float(x["total"] or 0) for x in cat_qs]

    return render(request, "analytics.html", {
        "year": year,
        "currency": currency,
        "labels": labels,
        "income": income,
        "expense": expense,
        "cat_labels": cat_labels,
        "cat_values": cat_values,
    })
