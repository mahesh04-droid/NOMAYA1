from django.conf import settings

def currency_processor(request):
    currency = request.session.get('currency', 'INR')
    if currency not in settings.EXCHANGE_RATES:
        currency = 'INR'
        
    return {
        'active_currency': currency,
        'exchange_rates': settings.EXCHANGE_RATES
    }
