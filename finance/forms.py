from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Account, Category, Transaction, Comment, Transfer


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["type", "currency", "card_kind", "bank_name", "last4"]
        labels = {
            "type": _("Hisob turi"),
            "currency": _("Pul birligi"),
            "card_kind": _("Karta turi"),
            "bank_name": _("Bank nomi"),
            "last4": _("Kartaning oxirgi 4 raqami"),
        }

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get("type")

        if a == Account.CARD:
            if not cleaned.get("currency"):
                self.add_error("currency", _("Karta pul birligini tanlang."))
            if not cleaned.get("card_kind"):
                self.add_error("card_kind", _("Karta turini tanlang."))
            if not cleaned.get("bank_name"):
                self.add_error("bank_name", _("Bank nomini kiriting."))

            last4 = (cleaned.get("last4") or "").strip()
            if len(last4) != 4 or not last4.isdigit():
                self.add_error("last4", _("Oxirgi 4 raqamni to‘g‘ri kiriting (masalan: 1234)."))

        elif a == Account.CASH:
            if not cleaned.get("currency"):
                self.add_error("currency", _("Pul birligini tanlang."))
            cleaned["card_kind"] = None
            cleaned["bank_name"] = None
            cleaned["last4"] = None

        return cleaned


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "type"]
        labels = {
            "name": _("Nomi"),
            "type": _("Turi"),
        }


class TransactionForm(forms.ModelForm):
    currency = forms.ChoiceField(choices=Account.CURRENCY, required=True, label=_("Valyuta"))

    class Meta:
        model = Transaction
        fields = ["type", "category", "currency", "account", "amount", "date", "note"]
        labels = {
            "type": _("Turi"),
            "category": _("Kategoriya"),
            "account": _("Hisob"),
            "amount": _("Summa"),
            "date": _("Sana"),
            "note": _("Izoh (note)"),
        }
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields["category"].queryset = Category.objects.filter(user=self.user)
            self.fields["account"].queryset = Account.objects.filter(user=self.user)

        # update bo‘lsa currency ni account’dan to‘ldiramiz
        if self.instance and self.instance.pk and self.instance.account_id:
            self.fields["currency"].initial = self.instance.account.currency

        # POST bo‘lsa currency bo‘yicha accountlarni filtrlash
        cur = self.data.get("currency")
        if cur and self.user:
            self.fields["account"].queryset = Account.objects.filter(user=self.user, currency=cur)

        # account label’larni chiroyli qilish
        choices = []
        for acc in self.fields["account"].queryset:
            label = f"{acc.get_type_display()} - {acc.get_currency_display()}"
            choices.append((acc.pk, label))
        self.fields["account"].choices = choices

    def clean(self):
        cleaned = super().clean()
        cur = cleaned.get("currency")
        acc = cleaned.get("account")

        if self.user and acc and acc.user_id != self.user.id:
            self.add_error("account", _("Bu hisob sizga tegishli emas."))
            return cleaned

        if acc and cur and acc.currency != cur:
            self.add_error("account", _("Tanlangan hisob valyutasi currency bilan mos emas."))
        return cleaned


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        labels = {"text": _("Izoh matni")}


class TransferForm(forms.ModelForm):
    class Meta:
        model = Transfer
        fields = ["from_account", "to_account", "amount_from", "amount_to", "rate", "date", "note"]
        labels = {
            "from_account": _("Qayerdan"),
            "to_account": _("Qayerga"),
            "amount_from": _("Yuborilgan summa"),
            "amount_to": _("Qabul qilingan summa"),
            "rate": _("Kurs"),
            "date": _("Sana"),
            "note": _("Izoh (note)"),
        }
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user:
            qs = Account.objects.filter(user=self.user)
            self.fields["from_account"].queryset = qs
            self.fields["to_account"].queryset = qs

    def clean(self):
        cleaned = super().clean()
        fa = cleaned.get("from_account")
        ta = cleaned.get("to_account")
        if fa and ta and fa.id == ta.id:
            self.add_error("to_account", _("Bir xil hisob tanlab bo‘lmaydi."))
        return cleaned
