from django.core.paginator import Paginator, Page


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


class PaginatedObjectList(object):

    def __init__(self, object_list, total):
        self.object_list = object_list
        self.total = total

    def count(self):
        return self.total

    def __iter__(self):
        for obj in self.object_list:
            yield obj


class ESPaginator(Paginator):
    """
    Override the core Paginator so that it doesn't need a complete
    list of objects. Use the paginated result set from ES instead.
    """

    def page(self, number):
        # Data has been sliced already, just return the full list
        number = self.validate_number(number)
        return Page(self.object_list, number, self)
