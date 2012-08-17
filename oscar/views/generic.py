from django.utils.encoding import smart_str
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _


class PostActionMixin(object):
    """
    Simple mixin to forward POST request that contain a key 'action'
    onto a method of form "do_{action}".  
    
    This only works with DetailView
    """
    def post(self, request, *args, **kwargs):
        if 'action' in self.request.POST:
            model = self.get_object()
            # The do_* method is required to do what it needs to with the model
            # it is passed, and then to assign the HTTP response to self.response.
            method_name = "do_%s" % self.request.POST['action'].lower()
            if hasattr(self, method_name):
                getattr(self, method_name)(model)
                return self.response
            else:
                messages.error(request, _("Invalid form submission"))
        return super(PostActionMixin, self).post(request, *args, **kwargs)
    

class BulkEditMixin(object):
    """
    Mixin for views that have a bulk editing facility.  This is normally in the
    form of tabular data where each row has a checkbox.  The UI allows a number
    of rows to be selected and then some 'action' to be performed on them.
    """
    action_param = 'action'
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

    def get_error_url(self, request):
        return request.META['HTTP_REFERER']

    def get_success_url(self, request):
        return request.META['HTTP_REFERER']

    def post(self, request, *args, **kwargs):
        # Dynamic dispatch pattern - we forward POST requests onto a method
        # designated by the 'action' parameter.  The action has to be in a
        # whitelist to avoid security issues.
        action = request.POST.get(self.action_param, '').lower()
        if not self.actions or action not in self.actions:
            messages.error(self.request, _("Invalid action"))
            return HttpResponseRedirect(self.get_error_url(request))

        ids = request.POST.getlist('selected_%s' % self.get_checkbox_object_name())
        if not ids:
            messages.error(self.request, _("You need to select some %ss") % self.get_checkbox_object_name())
            return HttpResponseRedirect(self.get_error_url(request))

        raw_objects = self.model.objects.in_bulk(ids)
        objects = [raw_objects[int(id)] for id in ids]
        return getattr(self, action)(request, objects)

