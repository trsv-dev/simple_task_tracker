def excluded_urls(request):
    return {
        'excluded_urls': ['login', 'logout', 'register', 'password_reset',
                          'password_change', 'password_change_done',
                          'password_reset_complete', 'password_reset_done',
                          'password_reset_confirm']
    }
