def urls_without_menu_and_auth(request):
    return {
        'urls_without_menu_and_auth': [
            'core/403.html',
            'core/404.html',
            'core/500.html',
            'core/403csrf.html'
        ]
    }
