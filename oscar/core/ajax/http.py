from django.http import HttpResponse
import simplejson as json


class JsonResponse(HttpResponse):
    def __init__(self, content='', mimetype='application/javascript', status=None,
                 content_type=None):
        self.dict_content = content
        super(JsonResponse, self).__init__(content, mimetype, status, content_type)

    def render(self):
        return json.dumps(self.dict_content)
