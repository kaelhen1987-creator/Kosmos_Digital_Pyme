def format_currency(value):
    """Formatea numero a moneda (CLP/USD style)"""
    try:
        return f"${value:,.0f}".replace(",", ".")
    except:
        return f"${value}"
