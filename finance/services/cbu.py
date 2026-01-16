# finance/services/cbu.py
from decimal import Decimal
from datetime import datetime
import requests

from finance.models import ExchangeRate

CBU_URL = "https://cbu.uz/uz/arkhiv-kursov-valyut/json/"  # rasmiy JSON :contentReference[oaicite:1]{index=1}

def update_usd_uzs():
    """
    CBU’dan USD kursini olib, ExchangeRate(base='USD', quote='UZS') qilib saqlaydi.
    Return: (obj, created)
    """
    resp = requests.get(CBU_URL, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    usd = next((x for x in data if x.get("Ccy") == "USD"), None)
    if not usd:
        raise RuntimeError("CBU javobida USD topilmadi")

    # CBU odatda: Rate="11969.66", Date="16.01.2026"
    rate = Decimal(str(usd["Rate"]).replace(",", "."))
    rate_date = datetime.strptime(usd["Date"], "%d.%m.%Y").date()

    obj, created = ExchangeRate.objects.update_or_create(
        base="USD",
        quote="UZS",
        date=rate_date,
        defaults={"rate": rate},
    )
    return obj, created
