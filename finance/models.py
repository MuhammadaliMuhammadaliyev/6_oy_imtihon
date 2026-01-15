from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Account(models.Model):
    ACCOUNT_TYPES = (
        ("CASH", "Naqd pul"),
        ("CARD", "Karta"),
    )

    CURRENCY = (
        ("UZS", "So'm"),
        ("USD", "Dollar"),
    )

    CARD_KINDS = (
        ("UZCARD", "Uzcard"),
        ("HUMO", "Humo"),
        ("VISA", "Visa"),
        ("MC", "Mastercard"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="accounts")
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=4, choices=ACCOUNT_TYPES)
    currency = models.CharField(max_length=3, choices=CURRENCY, blank=True, null=True)
    card_kind = models.CharField(max_length=10, choices=CARD_KINDS, blank=True, null=True)
    bank_name = models.CharField(max_length=80, blank=True, null=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return self.type


class Category(models.Model):
    Category_types = (
        ("IN", "Kirim"),
        ("EX", "Chiqim"),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=3, choices=Category_types)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(models.Model):
    Tran_types = (
        ("IN", "Kirim"),
        ("EX", "Chiqim"),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=3, choices=Tran_types)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount}"


class Comment(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)