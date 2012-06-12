from oscar.core.ajax.http import JsonResponse

from django.contrib import messages


class AjaxMiddleware(object):
    def process_template_response(self, request, response):
        if request.is_ajax() and isinstance(response, JsonResponse):
            django_messages = []

            for message in messages.get_messages(request):
                django_messages.append({ 
                    "level": message.level,
                    "message": unicode(message.message),
                    "extra_tags": message.tags,
                    })
            response.dict_content['django_messages'] = django_messages
        return response
