from django.http import HttpResponse
import simplejson as json

class JsonResponse(HttpResponse):
    def __init__(self, dict_content=None, mimetype='application/json', status=None, content_type=None):
        self.dict_content = dict_content if dict_content else {}
        if type(self.dict_content) is not dict:
            raise TypeError('JsonResponse content argument must be a dictionary')
        super(JsonResponse, self).__init__('', mimetype, status, content_type)

    def render(self):
        self.content = json.dumps(self.dict_content)
        return self
