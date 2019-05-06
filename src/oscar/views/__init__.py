from django.shortcuts import render


def handler403(request, exception):
    return render(request, 'oscar/403.html', status=403)


def handler404(request, exception):
    return render(request, 'oscar/404.html', status=404)


def handler500(request):
    return render(request, 'oscar/500.html', status=500)


def sort_queryset(queryset, request, allowed_sorts, default=None):
    """ Sorts the queryset by one of allowed_sorts based on parameters
    'sort' and 'dir' from request """
    sort = request.GET.get('sort', None)
    if sort in allowed_sorts:
        direction = request.GET.get('dir', 'asc')
        sort = ('-' if direction == 'desc' else '') + sort
        queryset = queryset.order_by(sort)
    elif default:
        queryset = queryset.order_by(default)
    return queryset
