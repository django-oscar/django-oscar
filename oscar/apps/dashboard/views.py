from django.utils.encoding import smart_str
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView
from django.contrib import messages
from django.http import HttpResponseRedirect


class BulkEditMixin():
    """
    Mixin for views that have a bulk editing facility.  This is normally in the
    form of tabular data where each row has a checkbox.  The UI allows a number
    of rows to be selected and then some 'action' to be performed on them.
    """
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
        # Dynamic dispatch patter - we forward POST requests onto a method
        # designated by the 'action' parameter.  The action has to be in a
        # whitelist to avoid security issues.
        action = request.POST.get('action', '').lower()
        if not self.actions or action not in self.actions:
            messages.error(self.request, "Invalid action")
            return HttpResponseRedirect(reverse(self.current_view))
        ids = request.POST.getlist('selected_%s' % self.get_checkbox_object_name())
        if not ids:
            messages.error(self.request, "You need to select some %ss" % self.get_checkbox_object_name())
            return HttpResponseRedirect(reverse(self.current_view))

        raw_objects = self.model.objects.in_bulk(ids)
        objects = (raw_objects[int(id)] for id in ids)
        return getattr(self, action)(request, objects)


class IndexView(TemplateView):
    template_name = 'dashboard/index.html'
