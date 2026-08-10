"""
Shared formatting helpers for anything user-facing that involves money,
percentages, or large numbers — keeps "$4.2B" vs "$4,200,000,000" vs
"4.2 billion" consistent across alert messages, briefings, and research
answers instead of each call site formatting numbers its own way.
"""
from __future__ import annotations


def format_currency(value: float, currency: str = "USD") -> str:
    """4.2 -> '$4.20'. Only USD gets the $ symbol for now; extend the map for other currencies."""
    symbol = {"USD": "$"}.get(currency, "")
    return f"{symbol}{value:,.2f}"


def format_percent(value: float, show_sign: bool = True) -> str:
    """7.234 -> '+7.23%'; -3.1 -> '-3.10%'."""
    sign = "+" if show_sign and value > 0 else ""
    return f"{sign}{value:.2f}%"


def format_large_number(value: float) -> str:
    """
    1_234_567 -> '1.23M', 4_200_000_000 -> '4.20B'. Used for market cap,
    revenue, and other figures where the raw digit count is hard to parse
    at a glance in a chat message.
    """
    abs_value = abs(value)
    sign = "-" if value < 0 else ""

    if abs_value >= 1_000_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000_000:.2f}T"
    if abs_value >= 1_000_000_000:
        return f"{sign}{abs_value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"{sign}{abs_value / 1_000_000:.2f}M"
    if abs_value >= 1_000:
        return f"{sign}{abs_value / 1_000:.2f}K"
    return f"{sign}{abs_value:.2f}"


def format_price_move(price: float, change_percent: float, currency: str = "USD") -> str:
    """Common pattern across alert/briefing messages: '$250.00 (+7.20%)'."""
    return f"{format_currency(price, currency)} ({format_percent(change_percent)})"
