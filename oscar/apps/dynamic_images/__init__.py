from oscar.apps.dynamic_images.cache import DiskCache
from oscar.apps.dynamic_images.exceptions import ResizerConfigurationError, \
    ResizerSyntaxError, ResizerFormatError
from oscar.apps.dynamic_images.mods import AutotrimMod, CropMod, ResizeMod
from oscar.apps.dynamic_images.response_backends import DirectResponse
from wsgiref.util import request_uri, application_uri
import Image
import cStringIO
import datetime
import math
import os
import sys
import re

try:
    import cStringIO as StringIO
except:
    import StringIO

def get_class(kls):
    try:
        parts = kls.split('.')
        module = ".".join(parts[:-1])
        m = __import__(module)
        for comp in parts[1:]:
            m = getattr(m, comp)
        return m
    except (ImportError, AttributeError), e:
        raise ResizerConfigurationError('Error importing class "%s"' % kls)


def error404(path, start_response):
    """ Returns an error 404 with text giving the requested URL. """
    status = '404 NOT FOUND'
    output = '404: File Not Found: ' + path + '\n'

    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)

    return [output]


def error500(path, e, start_response):
    """ Returns an error 500 with text giving the requested URL. """
    status = '500 Exception'
    output = '500: ' + str(e) + '\n'

    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)

    return [output]


class ImageModifier(object):
    """
    Modifies an image and saves to a cache location

    Output Formats:

    extension => ('format', 'mime-type')

    the key is the extension appended to the URL,
    the value tuple holds PIL's name for the format and the mime-type to serve
    with
    """
    output_formats = {
        'jpeg': ('JPEG', 'image/jpeg'),
        'jpg': ('JPEG', 'image/jpeg'),
        'gif': ('GIF', 'image/gif'),
        'png': ('PNG', 'image/png'),
    }

    # When we process an image, these modifications are applied in order
    installed_modifications = (
        AutotrimMod,
        CropMod,
        ResizeMod,
    )

    quality = 80
    
    process_check = re.compile(r'^(?P<filename>.+?)\.(?P<params>[a-z0-9]+-[a-z0-9]+(.+?)*)\.(?P<type>[a-z0-9]+)$').search
    convert_check = re.compile(r'^(?P<filename>.+?)\.to\.(?P<type>[a-z0-9]+)$').search

    def __init__(self, url, config):
        if config.get('installed_mods'):
            self.installed_modifications = config['installed_mods']

        self._url = url
        self._image_root = config['asset_root']
        self._process_path()

    def _process_path(self):
        """
        Extracts parameters from the image path

        Valid syntax:
        - /path/to/image.ext (serve image unchanged)
        - /path/to/image.ext.to.newext (change format of image)
        - /path/to/image.ext.options-string.newext (change format and modify
          image)

        Format of options string is:
        key1-value1_key2-value2_key3-value3
        """
        path, name = os.path.split(self._url)
        
        p_result = self.process_check(name)
        c_result = self.convert_check(name)
        
        if p_result:
            filename = p_result.group('filename')
            type = p_result.group('type')            
            params = p_result.group('params')
            
            param_parts = params.split('_')
            
            try:
                params = dict(
                    [(x.split("-")[0], x.split("-")[1]) for x in param_parts])
            except IndexError:
                raise ResizerSyntaxError("Invalid filename syntax")            
        elif c_result:
            filename = c_result.group('filename')            
            type = c_result.group('type')
            params = {}
        else:
            filename = self._url
            type = os.path.splitext(name)[1][1:]

            params = {}
        
        params['type'] = type
        
        self._params = params
        self.source_filename = os.path.join(path,filename)

        if self._params['type'] not in self.output_formats:
            raise ResizerFormatError("Invalid output format")

    def source_path(self):
        return os.path.join(self._image_root, self.source_filename)

    def generate_image(self):
        source = Image.open(self.source_path())

        if (self._params['type'] == 'png'):
            source = source.convert("RGBA")
        else:
            source = source.convert("RGB")

        # Iterate over the installed modifications and apply them to the image
        for mod in self.installed_modifications:
            source = mod(source, self._params).apply()

        output = StringIO.StringIO()

        source.save(output, self.get_type()[0], quality=self.quality)

        output.seek(0)
        data = output.read()

        return data

    def get_type(self):
        return self.output_formats[self._params['type']]
    
    def get_mime_type(self):
        return self.get_type()[1]


class BaseImageHandler(object):
    """
    This can be called by a WSGI script, or via DjangoImageHandler.
    Django version is handy for local development, but adds unnecessary
    overhead to production
    """
    modifier = ImageModifier
    cache = DiskCache
    response_backend = DirectResponse
    
    def build_sendfile_response(self, metadata, modifier, start_response):
        pass

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO')
        config = environ.get('MEDIA_CONFIG')

        # Don't bother processing stuff we know is invalid
        if path == '/' or path == '/favicon.ico':
            return error404(path, start_response)
        path = path[1:]

        if config.get('cache_backend'):
            self.cache = get_class(config['cache_backend'])
        if config.get('response_backend'):
            self.response_backend = get_class(config['response_backend'])
        if config.get('installed_mods'):
            mod_overrides = []
            for v in config['installed_mods']:
                mod_overrides.append(get_class(v))
            config.installed_mods = tuple(mod_overrides)            
            
        try:
            c = self.cache(path, config)
            m = self.modifier(path, config)
        except (ResizerSyntaxError, ResizerFormatError), e:
            return error500(path, e, start_response)
        try:
            if not c.check(m.source_path()):
                data = m.generate_image()
                c.write(data)
            return self.response_backend(config, m.get_mime_type(),c,start_response).build_response()
        except Exception, e:
            return error404(path, start_response)


class DjangoImageHandler(BaseImageHandler):

    def __call__(self, request):
        from django.http import HttpResponse
        from django.conf import settings

        env = request.META.copy()

        config = settings.DYNAMIC_MEDIA_CONFIG
        prefix = settings.DYNAMIC_URL_PREFIX

        env['MEDIA_CONFIG'] = config
        env['PATH_INFO'] = env['PATH_INFO'][len(prefix) + 1:]

        django_response = HttpResponse()

        def start_response(status, headers):
            status = status.split(' ', 1)[0]
            django_response.status_code = int(status)
            for header, value in headers:
                django_response[header] = value

        response = super(DjangoImageHandler, self).__call__(env, start_response)
        django_response.content = "\n".join(response)

        return django_response
