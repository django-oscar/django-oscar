
class PostActionMixin(object):
    """
    Simple mixin to forward POST request that contain a key 'action'
    onto a method of form "do_{action}".  This makes some DetailViews
    easier to write.
    """
    def post(self, request, *args, **kwargs):
        if 'action' in self.request.POST:
            model = self.get_object()
            getattr(self, "do_%s" % self.request.POST['action'].lower())(model)
            return self.response
    