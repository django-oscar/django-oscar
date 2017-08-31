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
