from oscar.core.loading import get_class

EventHandler = get_class('order.processing', 'EventHandler')


class EventHandlerMixin(object):
    """
    Handle EventHandler Class
    """

    handler_class = EventHandler

    def get_handler_class(self):
        """Return handler class to use"""
        return self.handler_class

    def get_handler(self, **kwargs):
        """Return instance of handler"""
        handler_kwargs = self.get_handler_kwargs()
        handler_kwargs.update(**kwargs)
        return self.get_handler_class()(**handler_kwargs)

    def get_handler_kwargs(self):
        """Return kwargs arguments for instantiating handler"""
        kwargs = dict()
        return kwargs
