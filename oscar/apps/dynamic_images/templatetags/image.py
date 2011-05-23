from django import template
from django.conf import settings
from django.db.models.fields.files import ImageFieldFile

register = template.Library()


def do_dynamic_image_url(parser, token):
    tokens = token.split_contents()

    if len(tokens) < 2:
        raise template.TemplateSyntaxError("%r tag requires at least an image URL or field" % tokens[0])

    image = tokens[1]

    if len(tokens) > 2:
        params = tokens[2:]
    else:
        params = []
    return DynamicImageNode(image, params)


class DynamicImageNode(template.Node):
    def __init__(self, image, params):
        self.image = image
        self.params = {}

        for p in params:
            try:
                bits = p.split('=')
                self.params[bits[0]] = template.Variable(bits[1])
            except IndexError:
                raise template.TemplateSyntaxError("image tag parameters must be of form key=value, you used '%s'" % p)

    def render(self, context):
        if isinstance(self.image, ImageFieldFile):
            path = self.image.name
        else:
            path = self.image

        host = getattr(settings,'DYNAMIC_MEDIA_URL', None)

        if host:
            params = []

            ext = path[path.rfind('.') + 1:]
            ext_changed = False
    
            for key, v in self.params.iteritems():
                value = v.resolve(context)
    
                if key == u'format':
                    ext = value
                    ext_changed = True
                else:
                    params.append('%s-%s' % (key, value))
    
            if len(params) > 0:
                suffix = '_'.join(params)
                path = '.'.join((path, suffix, ext))
            else:
                if ext_changed:
                    if params:
                        path = '.'.join((path, ext))
                    else:
                        path = '.'.join((path, 'to', ext))

    
            return host + path

register.tag('image', do_dynamic_image_url)
