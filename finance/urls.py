from django.urls import path
from .views import (dashboard, transaction_create, transaction_update, transaction_detail, transaction_delete,
                    account_list, account_create, account_update,
                    account_delete, category_list, category_create, category_update, category_delete, monthly_report,
                    transfer_create, )

app_name = "finance"

urlpatterns = [
    path('', dashboard, name="dashboard"),
    path('transactions/create/', transaction_create, name="transaction_create"),
    path('transactions/<int:pk>/update/', transaction_update, name="transaction_update"),
    path('transactions/<int:pk>/', transaction_detail, name="transaction_detail"),
    path('transactions/<int:pk>/delete/', transaction_delete, name="transaction_delete"),
    path("accounts/", account_list, name="account_list"),
    path("accounts/create/", account_create, name="account_create"),
    path("accounts/<int:pk>/update/", account_update, name="account_update"),
    path("accounts/<int:pk>/delete/", account_delete, name="account_delete"),
    path("categories/", category_list, name="category_list"),
    path("categories/create/", category_create, name="category_create"),
    path("categories/<int:pk>/update/", category_update, name="category_update"),
    path("categories/<int:pk>/delete/", category_delete, name="category_delete"),
    path("report/monthly/", monthly_report, name="monthly_report"),
    path("transfer/create/", transfer_create, name="transfer_create"),

]
