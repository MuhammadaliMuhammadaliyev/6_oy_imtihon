from django import forms
from .models import Account, Category, Transaction, Comment


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ["type", "currency", "card_kind", "bank_name", "last4"]

    def clean(self):
        cleaned = super().clean()
        a = cleaned.get("type")

        if a == "CARD":
            if not cleaned.get("currency"):
                self.add_error("currency", "Karta pul birligini tanlang.")
            if not cleaned.get("card_kind"):
                self.add_error("card_kind", "Karta turini tanlang.")
            if not cleaned.get("bank_name"):
                self.add_error("bank_name", "Bank nomini kiriting.")
            last4 = (cleaned.get("last4") or "").strip()
            if len(last4) != 4 or not last4.isdigit():
                self.add_error("last4", "Oxirgi 4 raqamni to‘g‘ri kiriting (masalan: 1234).")
        elif a in ("CASH", "CURR"):
            if not cleaned.get("currency"):
                self.add_error("currency", "Pul birligini tanlang.")
            cleaned["card_kind"] = None
            cleaned["bank_name"] = None
            cleaned["last4"] = None

        return cleaned



class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'type']


class TransactionForm(forms.ModelForm):
    currency = forms.ChoiceField(choices=Account.CURRENCY, required=True, label="Valyuta")

    class Meta:
        model = Transaction
        fields = ['type', 'category', 'currency', 'account', 'amount', 'date', 'note']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['category'].queryset = Category.objects.filter(user=self.user)
            self.fields['account'].queryset = Account.objects.filter(user=self.user)

        # update bo‘lsa currency ni account’dan to‘ldiramiz
        if self.instance and self.instance.pk and self.instance.account_id:
            self.fields['currency'].initial = self.instance.account.currency

        # POST bo‘lsa currency bo‘yicha accountlarni filtrlash
        cur = self.data.get('currency')
        if cur and self.user:
            self.fields['account'].queryset = Account.objects.filter(user=self.user, currency=cur)

        # account optionlarga data-currency qo‘shish (template JS uchun)
        self.fields['account'].widget.attrs.update({'id': 'id_account'})
        choices = []
        for acc in self.fields['account'].queryset:
            label = f"{acc.get_type_display()} - {acc.get_currency_display()}"
            choices.append((acc.pk, label))
        self.fields['account'].choices = choices

    def clean(self):
        cleaned = super().clean()
        cur = cleaned.get('currency')
        acc = cleaned.get('account')

        if self.user and acc and acc.user_id != self.user.id:
            self.add_error('account', "Bu hisob sizga tegishli emas.")
            return cleaned

        if acc and cur and acc.currency != cur:
            self.add_error('account', "Tanlangan hisob valyutasi currency bilan mos emas.")
        return cleaned


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

