from http import HTTPStatus

from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html',
                  {'path': request.path, 'current_template': 'core/404.html'},
                  status=HTTPStatus.NOT_FOUND
                  )


def server_error(request):
    return render(request, 'core/500.html',
                  {'current_template': 'core/500.html'},
                  status=HTTPStatus.FORBIDDEN
                  )


def permission_denied(request, exception):
    return render(request, 'core/403.html',
                  {'current_template': 'core/403.html'},
                  status=HTTPStatus.INTERNAL_SERVER_ERROR
                  )


def csrf_failure(request, reason=''):
    return render(request, 'core/403csrf.html',
                  {'current_template': 'core/403csrf.html'})
