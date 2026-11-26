import pytest

from pricewatch.normalize import normalize_title


def test_same_gpu_in_different_languages():
    names = [
        "Grafička kartica ASUS GeForce RTX 4070 SUPER DUAL OC 12GB GDDR6X",   # HR
        "ASUS Grafikkarte GeForce RTX 4070 Super Dual OC, 12 GB GDDR6X",      # DE
        "Karta graficzna ASUS GeForce RTX 4070 SUPER Dual OC 12GB GDDR6X",    # PL
        "Carte graphique ASUS GeForce RTX 4070 SUPER DUAL OC - 12 Go GDDR6X", # FR (Go = GB)
        "Tarjeta Gráfica Asus GeForce RTX 4070 Super Dual OC 12GB GDDR6X",    # ES
    ]
    expected = "asus geforce rtx 4070 super dual oc 12gb gddr6x"
    for name in names:
        assert normalize_title(name) == expected, name


@pytest.mark.parametrize(
    "title, expected",
    [
        ("Samsung 990 PRO 2 TB NVMe SSD", "samsung 990 pro 2tb nvme ssd"),
        ('Monitor LG 27" UltraGear 27GR75Q', "monitor lg 27in ultragear 27gr75q"),
        ("LG Monitor 27 Zoll UltraGear 27GR75Q", "lg monitor 27in ultragear 27gr75q"),
        ("Kingston FURY 32GB (2x16GB) DDR5 6000MHz", "kingston fury 32gb 2x16gb ddr5 6000mhz"),
        ("Procesor AMD Ryzen 7 7800X3D + POKLON igra", "amd ryzen 7 7800x3d igra"),
        ("Dell 27,5 inch monitor", "dell 27.5in monitor"),
        ("Myš Logitech G502 – černá", "mys logitech g502 cerna"),
        ("Pamięć RAM Corsair 16 GB", "ram corsair 16gb"),
        ("Disque SSD Samsung 990 PRO 2 To", "ssd samsung 990 pro 2tb"),
    ],
)
def test_normalize_title(title, expected):
    assert normalize_title(title) == expected


def test_different_capacity_stays_different():
    a = normalize_title("Samsung 990 PRO 1TB")
    b = normalize_title("Samsung 990 PRO 2TB")
    assert a != b


def test_empty_title():
    assert normalize_title("") == ""
    assert normalize_title(None) == ""
