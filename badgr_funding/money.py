"""Money as integer cents. Missing stays None; never defaults to zero."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def to_cents(value):
    """Parse '$5,550.00', '-17084', 1200.5 or Decimal into integer cents; blank -> None."""
    if value is None:
        return None
    if isinstance(value, int) and not isinstance(value, bool):
        return value * 100
    text = str(value).strip().replace("$", "").replace(",", "")
    if text == "":
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    try:
        amount = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"not a money value: {value!r}")
    cents = int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def fmt(cents):
    if cents is None:
        return "unknown"
    sign = "-" if cents < 0 else ""
    whole, part = divmod(abs(cents), 100)
    return f"{sign}${whole:,}.{part:02d}"


def range_text(min_cents, max_cents):
    if min_cents is None and max_cents is None:
        return "amount unknown"
    if min_cents == max_cents:
        return fmt(min_cents)
    return f"{fmt(min_cents) if min_cents is not None else '?'} – {fmt(max_cents) if max_cents is not None else '?'}"
