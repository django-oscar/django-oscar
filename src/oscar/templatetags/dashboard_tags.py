from django import template

from oscar.core.compat import assignment_tag
from oscar.core.loading import get_class

get_nodes = get_class('dashboard.menu', 'get_nodes')
register = template.Library()


@assignment_tag(register)
def dashboard_navigation(user, request):
    global URL_PATH
    URL_PATH = request.path
    return get_nodes(user)


@register.inclusion_tag('dashboard/navigation.html')
def draw_navigation(request, item, menu_items):
    # nav_items = []
    for menu_item in menu_items:
        # print(vars(menu_item))
        menu_item.active = False
        if menu_item.url_name is not None:
            menu_item.active = menu_item.url == request.path
        if menu_item.has_children:
            for sub_item in menu_item.children:
                if sub_item.url_name is not None and sub_item.url == request.path:
                    menu_item.active = True
                    sub_item.active = True

    return {
        "nav_items": menu_items,
        "item": item,
    }
