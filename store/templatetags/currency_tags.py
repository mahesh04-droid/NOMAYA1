from django import template
from django.conf import settings
from decimal import Decimal

register = template.Library()

@register.filter
def currency(value, currency_code):
    try:
        value = Decimal(str(value))
    except (ValueError, TypeError):
        return value
        
    rates = getattr(settings, 'EXCHANGE_RATES', {})
    if currency_code not in rates:
        currency_code = 'INR'
        
    rate_info = rates.get(currency_code, {'rate': 1.0, 'symbol': '₹'})
    converted = value * Decimal(str(rate_info['rate']))
    
    # Format
    if converted % 1 == 0:
        formatted = f"{converted:,.0f}"
    else:
        formatted = f"{converted:,.2f}"
        
    return f"{rate_info['symbol']}{formatted}"
