"""Pretvaranje teksta cijene u broj, za formate koji se koriste u europskim trgovinama.

Primjeri:
    "1.299,99 €"   -> Decimal("1299.99")   (HR, DE, NL, ES)
    "1 299,99 zł"  -> Decimal("1299.99")   (PL, FR, CZ – razmak kao separator tisućica)
    "€1,299.99"    -> Decimal("1299.99")   (engleski zapis)
    "12 990,- Kč"  -> Decimal("12990")     (CZ – ",-" znači bez decimala)
"""

import re
from decimal import Decimal, InvalidOperation

# Razmaci koji se pojavljuju kao separator tisućica (obični, neprekidivi, uski neprekidivi)
_SPACES = "    "

# Prvi niz znamenki sa separatorima, npr. "1.299,99" ili "1 299,99"
_NUMBER_RE = re.compile(r"\d[\d" + _SPACES + r".,']*")


def parse_price(value) -> Decimal | None:
    """Vraća cijenu kao Decimal ili None ako u tekstu nema cijene.

    Prima i brojeve (int, float) jer JSON-LD cijenu ponekad daje kao broj.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))

    text = str(value).replace(",-", "").replace(",–", "")
    match = _NUMBER_RE.search(text)
    if not match:
        return None

    number = match.group().strip(_SPACES + ".,'")
    for ch in _SPACES + "'":
        number = number.replace(ch, "")

    decimal_sep = _guess_decimal_separator(number)
    if decimal_sep is None:
        number = number.replace(".", "").replace(",", "")
    else:
        thousands_sep = "," if decimal_sep == "." else "."
        number = number.replace(thousands_sep, "").replace(decimal_sep, ".")

    try:
        return Decimal(number)
    except InvalidOperation:
        return None


def _guess_decimal_separator(number: str) -> str | None:
    """Određuje je li decimalni separator točka, zarez ili ga nema.

    Pravila:
    - ako se pojavljuju i točka i zarez, decimalni je onaj koji je zadnji;
    - ako se separator pojavljuje više puta, to su tisućice ("1.299.000");
    - ako se pojavljuje jednom i iza njega su 1–2 znamenke, decimalni je ("19,99");
    - ako su iza njega točno 3 znamenke, smatra se separatorom tisućica ("1.299").
    """
    has_dot, has_comma = "." in number, "," in number

    if has_dot and has_comma:
        return "." if number.rfind(".") > number.rfind(",") else ","

    sep = "." if has_dot else "," if has_comma else None
    if sep is None:
        return None
    if number.count(sep) > 1:
        return None

    digits_after = len(number) - number.index(sep) - 1
    return None if digits_after == 3 else sep
