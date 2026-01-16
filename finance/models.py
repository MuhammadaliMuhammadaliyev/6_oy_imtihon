from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Account(models.Model):
    # -------- Choices (TRANSLATABLE) --------
    CASH = "CASH"
    CARD = "CARD"
    ACCOUNT_TYPES = (
        (CASH, _("Naqd pul")),
        (CARD, _("Karta")),
    )

    UZS = "UZS"
    USD = "USD"
    CURRENCY = (
        (UZS, _("So'm")),
        (USD, _("Dollar")),
    )

    UZCARD = "UZCARD"
    HUMO = "HUMO"
    VISA = "VISA"
    MC = "MC"
    CARD_KINDS = (
        (UZCARD, _("Uzcard")),
        (HUMO, _("Humo")),
        (VISA, _("Visa")),
        (MC, _("Mastercard")),
    )

    # -------- Fields --------
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)

    type = models.CharField(max_length=4, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, choices=CURRENCY, blank=True, null=True)

    card_kind = models.CharField(max_length=10, choices=CARD_KINDS, blank=True, null=True)
    bank_name = models.CharField(max_length=80, blank=True, null=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        # Admin + template uchun chiroyli
        parts = [self.name or self.get_type_display()]
        if self.currency:
            parts.append(self.currency)
        if self.type == self.CARD and self.card_kind:
            parts.append(self.card_kind)
        return " • ".join(parts)


class Category(models.Model):
    IN_ = "IN"
    EX_ = "EX"
    CATEGORY_TYPES = (
        (IN_, _("Kirim")),
        (EX_, _("Chiqim")),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=3, choices=CATEGORY_TYPES)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    IN_ = "IN"
    EX_ = "EX"
    TRAN_TYPES = (
        (IN_, _("Kirim")),
        (EX_, _("Chiqim")),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=TRAN_TYPES)

    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    currency = models.CharField(max_length=3, choices=Account.CURRENCY, blank=True, null=True)

    class Meta:
        ordering = ["-date", "-id"]

    def save(self, *args, **kwargs):
        if self.account_id and not self.currency:
            self.currency = self.account.currency
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount}"


class Comment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Transfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_account = models.ForeignKey("Account", on_delete=models.CASCADE, related_name="transfers_out")
    to_account = models.ForeignKey("Account", on_delete=models.CASCADE, related_name="transfers_in")

    amount_from = models.DecimalField(max_digits=15, decimal_places=2)
    amount_to = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    rate = models.DecimalField(max_digits=15, decimal_places=6, blank=True, null=True)

    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    out_tx = models.OneToOneField(
        "Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="transfer_out"
    )
    in_tx = models.OneToOneField(
        "Transaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="transfer_in"
    )

    def clean(self):
        if self.from_account_id == self.to_account_id:
            raise ValidationError(_("Bir xil hisobga transfer qilib bo‘lmaydi."))

        if self.from_account.user_id != self.user_id or self.to_account.user_id != self.user_id:
            raise ValidationError(_("Hisoblar sizga tegishli bo‘lishi shart."))

        if self.from_account.currency == self.to_account.currency:
            self.amount_to = self.amount_from
            self.rate = None
        else:
            if self.amount_to is None:
                raise ValidationError(_("Valyuta har xil bo‘lsa amount_to (qabul qilingan summa) kiriting."))

    def __str__(self):
        return f"Transfer {self.amount_from} {self.from_account.currency} -> {self.amount_to} {self.to_account.currency}"


class ExchangeRate(models.Model):
    base = models.CharField(max_length=3, choices=Account.CURRENCY, default=Account.USD)
    quote = models.CharField(max_length=3, choices=Account.CURRENCY, default=Account.UZS)
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    date = models.DateField()

    class Meta:
        unique_together = ("base", "quote", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date}: 1 {self.base} = {self.rate} {self.quote}"
