from django.shortcuts import render

from contacts.contacts import COMPANY_INFO


def privacy_policy(request):
    """
    Страница политики конфиденциальности
    """
    context = {
        'title': f'{COMPANY_INFO["NAME"]} - Политика конфиденциальности',
        'company_info': COMPANY_INFO,
    }
    return render(request, 'privacy/privacy.html', context)
