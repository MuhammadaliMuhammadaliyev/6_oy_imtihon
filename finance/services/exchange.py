from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from finance.models import ExchangeRate

def _q(d: Decimal) -> Decimal:
    return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def get_rate(base: str, quote: str, on_date=None) -> Decimal:
    if base == quote:
        return Decimal("1")

    if on_date is None:
        on_date = timezone.localdate()

    rate_obj = (
        ExchangeRate.objects
        .filter(base=base, quote=quote, date__lte=on_date)
        .first()
    )

    if not rate_obj:
        raise ValueError(f"Kurs topilmadi: {base}->{quote}")

    return rate_obj.rate

def convert(amount: Decimal, base: str, quote: str, on_date=None) -> Decimal:
    return _q(amount * get_rate(base, quote, on_date))
