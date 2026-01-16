from django.contrib import admin
from .models import Account, Category, Transaction, Comment
from .models import ExchangeRate
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect

from .models import ExchangeRate
from finance.services.cbu import update_usd_uzs

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("date", "base", "quote", "rate")
    list_filter = ("base", "quote")
    ordering = ("-date",)

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("update-cbu/", self.admin_site.admin_view(self.update_from_cbu), name="exchange_rate_update_cbu"),
        ]
        return custom + urls

    def update_from_cbu(self, request):
        try:
            obj, created = update_usd_uzs()
            msg = f"CBU’dan yangilandi: 1 {obj.base} = {obj.rate} {obj.quote} ({obj.date})"
            self.message_user(request, msg, level=messages.SUCCESS)
        except Exception as e:
            self.message_user(request, f"Xatolik: {e}", level=messages.ERROR)

        return redirect("..")


admin.site.register(Account)
admin.site.register(Category)
admin.site.register(Transaction)
admin.site.register(Comment)
