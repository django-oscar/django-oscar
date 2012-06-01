Returning JSON in views
========================

JsonResponse
------------
If you want to extend your views to work with ajax you may choose to return json data in your resposne.
To make this easier you can use ``JsonResposne`` found in the ``oscar.core.ajax`` package.::

    from oscar.core.ajax.http import JsonResponse

    class MyView(TemplateView):

        def get(self, request, *args, **kwargs):
            if request.is_ajax:
                context = self.get_context_data()
                return JsonResponse(context)
            # ...

This will set the correct mimetype (``application/json``) and serialise your context data into a json object.

Ajax Middleware
---------------
If you're using Django's messages framework, you can also add ``oscar.core.ajax.middleware.AjaxMiddleware`` in your
middlewares. This will inject all messages generated in your request into your ``JsonResponse`` object::

    from django.contrib import messages
    from oscar.core.ajax.http import JsonResponse

    class MyView(TemplateView):

        def get(self, request, *args, **kwargs):
            if request.is_ajax:
                context = self.get_context_data()

                messages.info(request, "This is very useful")
                messages.warning(request, "Be careful!")

                return JsonResponse(context)
            # ...

This would be rendered as the following::

    {
        //...
        'django_messages': [
            {"extra_tags": "info",
             "message": "This is very useful",
             "level": 20},
            {"extra_tags": "warning",
             "message": "Be careful!",
             "level": 30}
        ]
    }