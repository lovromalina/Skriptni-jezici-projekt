"""Normalizacija naziva proizvoda za usporedbu među trgovinama.

Ista grafička kartica u različitim trgovinama zove se npr.:
    "Grafička kartica ASUS GeForce RTX 4070 SUPER DUAL OC 12GB GDDR6X"
    "ASUS Grafikkarte GeForce RTX 4070 Super Dual OC, 12 GB GDDR6X"
    "Karta graficzna ASUS GeForce RTX 4070 SUPER Dual OC 12GB GDDR6X"
Nakon normalizacije svi daju isti niz, pa se mogu uspoređivati.
"""

import re
import unicodedata

# Riječi koje opisuju kategoriju ili su marketinške, na jezicima praćenih trgovina.
# Uklanjaju se jer se razlikuju po jeziku, a ne govore ništa o samom artiklu.
STOPWORDS = {
    # kategorije – grafička kartica
    "graficka", "kartica", "grafikkarte", "karta", "graficzna",
    "carte", "graphique", "tarjeta", "grafica", "videokaart", "videokarta",
    # kategorije – procesor, disk, memorija, monitor
    "procesor", "prozessor", "processeur", "procesador", "processor",
    "disk", "festplatte", "dysk", "disque", "disco", "schijf",
    "memorija", "arbeitsspeicher", "pamiec", "memoire", "memoria", "geheugen",
    "pamet", "operacni",
    # marketinške riječi
    "akcija", "novo", "poklon", "gratis", "neu", "nouveau", "nuevo", "nieuw",
    "nowosc", "novinka", "sale", "promo", "promocja", "oferta", "angebot",
    # veznici i prijedlozi koji se često pojavljuju u nazivima
    "i", "s", "sa", "za", "und", "mit", "fur", "et", "avec", "pour", "y", "con",
    "para", "en", "met", "voor", "z", "do", "a",
}
# Napomena: češko "pro" (= za) namjerno nije na popisu jer je često dio
# naziva modela (npr. "Samsung 990 PRO").

# Ujednačavanje jedinica: "12 GB" -> "12gb", "12 Go" (FR) -> "12gb", "27 Zoll" / 27" -> "27in"
_UNIT_PATTERNS = [
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*go\b"), r"\1gb"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*to\b"), r"\1tb"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(tb|gb|mb)\b"), r"\1\2"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(mhz|ghz|hz|w|mah)\b"), r"\1\2"),
    (re.compile(r"(\d+(?:[.,]\d+)?)\s*(\"|''|”|inch|inc|zoll|cali|cala|pouces|pulgadas|palcu)(?=\s|$|[^\w])"), r"\1in"),
]


def normalize_title(title: str) -> str:
    """Vraća normalizirani naziv: mala slova, bez dijakritika, ujednačene jedinice,
    bez riječi kategorije i marketinških riječi, tokeni odvojeni jednim razmakom.
    """
    if not title:
        return ""

    text = _strip_diacritics(title.lower())
    text = text.replace("ł", "l").replace("ß", "ss")  # znakovi koje NFKD ne rastavlja

    for pattern, repl in _UNIT_PATTERNS:
        text = pattern.sub(repl, text)

    # decimalni zarez u brojevima ("27,5in") ostaje kao točka, ostali znakovi postaju razmak
    text = re.sub(r"(\d),(\d)", r"\1.\2", text)
    text = re.sub(r"[^a-z0-9.\s]", " ", text)
    text = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", text)  # točka koja nije unutar broja

    tokens = [t for t in text.split() if t not in STOPWORDS]
    return " ".join(tokens)


def _strip_diacritics(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))
