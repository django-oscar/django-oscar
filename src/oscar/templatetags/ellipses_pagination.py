import warnings

from django import template

from oscar.core.utils import RemovedInOscar15Warning

register = template.Library()


@register.filter(name='ellipses_page_range')
def ellipses_page_range(page, args="1,2"):
    """
    Creates digg-style page_range for pagination

    Paginator.page_range returns range of all page numbers. For very long
    lists it isn't suitable (displaying hundereds of page numbers). This filter
    ellipses unimportant page numbers.

    Filter has two parameters:
      * AT_BORDERS: how many first/last pages do you want to show?
      * ARROUND_CURRENT: how many pages to the left/right from the current page
        do you want to show?

    Range consits of 5 parts:
    <first N pages> <ellipses> <around current page> <ellipses> <last N pages>

    Parts collide sometimes, e.g. when current page is the first one. Filter
    prevents putting the same page number twice in the range.

    Ellipses has to substitue at least two page numbers so something like
    [1, None, 3, 4, 5, 6, 7, None, 10] doesn't happen (it is more meaningful
    to have 2 instead of None).

    list(range()) is used for subrange generation because Python3 would return
    generators instead of lists.

    :param page: django's Page object for constructing the range
    :param args: optional arguments separated by ',' -- first is the number of
        pages at borders (N first pages, N last pages); second is the number of
        pages to the left/right from the current page.
    :returns: range of page numbers or None for ellipsed page numbers

    """

    warnings.warn(
        "The ellipses_page_range template filter will be removed in " +
        "Oscar 1.5. Please use django-rangepaginator instead",
        RemovedInOscar15Warning)

    if ',' not in args or len(args.split(',')) != 2:
        raise template.TemplateSyntaxError("Invalid number of arguments")

    AT_BORDERS, AROUND_CURRENT = (int(arg.strip()) for arg in args.split(','))

    page_num = page.number
    num_pages = page.paginator.num_pages

    # Compute borders
    first_start = 1
    first_end = first_start + AT_BORDERS
    middle_start = max(first_end, page_num - AROUND_CURRENT)
    middle_end = min(page_num + AROUND_CURRENT + 1, num_pages)
    last_start = max(middle_end, num_pages - AT_BORDERS + 1)
    last_end = num_pages + 1

    # first
    page_range = list(range(first_start, first_end))

    # border between first and middle
    if first_end + 1 < middle_start:
        page_range.append(None)
    elif first_end + 1 == middle_start:
        page_range.append(first_end)

    # middle
    page_range += list(range(middle_start, middle_end))

    # border between middle and last
    if middle_end + 1 < last_start:
        page_range.append(None)
    elif middle_end + 1 == last_start:
        page_range.append(middle_end)

    # last
    page_range += list(range(last_start, last_end))

    return page_range
