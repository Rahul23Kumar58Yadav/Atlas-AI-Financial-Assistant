from src.utils.formatting import format_currency, format_large_number, format_percent, format_price_move


def test_format_currency_basic():
    assert format_currency(4.2) == "$4.20"


def test_format_currency_thousands_separator():
    assert format_currency(1234.5) == "$1,234.50"


def test_format_percent_positive_shows_sign():
    assert format_percent(7.234) == "+7.23%"


def test_format_percent_negative():
    assert format_percent(-3.1) == "-3.10%"


def test_format_percent_no_sign_requested():
    assert format_percent(5.0, show_sign=False) == "5.00%"


def test_format_large_number_billions():
    assert format_large_number(4_200_000_000) == "4.20B"


def test_format_large_number_millions():
    assert format_large_number(1_234_567) == "1.23M"


def test_format_large_number_negative():
    assert format_large_number(-500) == "-500.00"


def test_format_price_move_combines_both():
    assert format_price_move(250.0, 7.2) == "$250.00 (+7.20%)"
