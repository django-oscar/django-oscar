from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView


class BulkEditMixin():
    actions = None
    current_view = None
    checkbox_object_name = None

    def get_checkbox_object_name(self):
        object_list = self.get_queryset()
        if self.checkbox_object_name:
            return self.checkbox_object_name
        elif hasattr(object_list, 'model'):
            return smart_str(object_list.model._meta.object_name.lower())
        else:
            return None

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '').lower()
        if action not in self.actions:
            messages.error(self.request, "Invalid action")
            return HttpResponseRedirect(reverse(self.current_view))
        ids = request.POST.getlist('selected_%s' % self.get_checkbox_object_name())
        if not ids:
            messages.error(self.request, "You need to select some %s" % self.get_checkbox_object_name())
            return HttpResponseRedirect(reverse(self.current_view))

        raw_objects = self.model.objects.in_bulk(ids)
        objects = (raw_objects[int(id)] for id in ids)
        return getattr(self, action)(request, objects)


class IndexView(TemplateView):
    template_name = 'dashboard/index.html'

    class MenuItem(object):
        def __init__(self, description, view_name):
            self.description = description
            self.url = reverse(view_name)

    def get_menu_items(self):
        MenuItem = IndexView.MenuItem
        # This needs to be configurable per project and permission based
        return (
            MenuItem('See order statistics', 'dashboard:order-summary'),
            MenuItem('Manage orders', 'dashboard:order-list'),
            MenuItem('View reports', 'dashboard:reports-index'),
            MenuItem('User management', 'dashboard:users-index'),
            MenuItem('Content block management', 'dashboard:promotion-list'),
            MenuItem('Catalogue management', 'dashboard:catalogue-product-list'),
        )

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['menu_items'] = self.get_menu_items()
        return context
