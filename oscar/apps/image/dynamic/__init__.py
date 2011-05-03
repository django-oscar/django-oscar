import sys, os, math, datetime
import Image, ImageEnhance, ImageOps, ImageChops
import cStringIO
from wsgiref.util import request_uri, application_uri

try:
    import cStringIO as StringIO
except:
    import StringIO

class ResizerSyntaxException(Exception):
    pass

class ResizerFormatException(Exception):
    pass

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

class BaseModification(object):
    
    def __init__(self,image,params):
        self._params = params
        self._image = image
    
    def apply(self):
        pass

class AutotrimMod(BaseModification):
    def apply(self):
        param_keys = self._params.keys()
        
        if ('width' in param_keys or 'height' in param_keys) and not 'crop' in param_keys:
            bg = Image.new(self._image.mode, self._image.size, (255,255,255,255))
            diff = ImageChops.difference(self._image, bg)
            bbox = diff.getbbox()

            return self._image.crop(bbox)
        return self._image
                    
class CropMod(BaseModification):
    def apply(self):
        if 'crop' in self._params.keys():
            crop = self._params['crop']
            bounds = tuple(int(x) for x in crop.split(','))
            return self._image.crop(bounds)
        return self._image

class ResizeMod(BaseModification):
    def apply(self):
        param_keys = self._params.keys()
        
        if 'width' in param_keys or 'height' in param_keys:
            w = self._params.get('width',None)
            h = self._params.get('height',None)
            
            target_w = float(w) if w else None
            target_h = float(h) if h else None
            
            source_w, source_h = [float(v) for v in self._image.size]
            
            scale = 1.0
            
            if target_w:
                temp_scale = target_w / source_w
                if temp_scale < scale:
                    scale = temp_scale
            if target_h:
                temp_scale = target_h / source_h
                if temp_scale < scale:
                    scale = temp_scale
                    
            if scale < 1.0:
                new_size = (int(round(source_w * scale)),
                            int(round(source_h * scale)))
                self._image = self._image.resize(new_size,Image.ANTIALIAS)
            
            new_w = int(target_w if target_w else self._image.size[0])
            new_h = int(target_h if target_h else self._image.size[1])
            
            bg = Image.new(self._image.mode, (new_w,new_h), (255,255,255,255))
            
            left = int(math.floor(float(new_w - self._image.size[0])/2))
            top = int(math.floor(float(new_h-self._image.size[1])/2))
            
            bg.paste(self._image, (left, top))
                
            return bg
        return self._image
    
class BaseCache(object):
    
    def __init__(self,path,config):
        self._path = path
        self._config = config
    
    def check(self, path):
        return False
    
    def write(self, data):
        pass
    
    def read(self):
        pass

class DiskCache(BaseCache):
    
    def _create_folders(self):
        """
        Create the disk cache path so that the cached image can be stored in the
        same hierarchy as the original images.
        """
        paths = self._path.split(os.path.sep)
        paths.pop() # Remove file from path
        path = os.path.join(self._config['cache_root'],*paths)
        
        if not os.path.isdir(path):
            os.makedirs(path)
                
    def _cache_path(self):
        return os.path.join(self._config['cache_root'],self._path)
                
    def check(self,path):
        """
        Checks the disk cache for an already processed image. If it exists then
        we'll check it's timestamp against the original image to make sure it's
        newer (and therefore valid). Also creates the folder hierarchy in the cache
        for the cached image if it doesn't find it there itself.
        """        
        self._create_folders()

        cache = self._cache_path()
        
        original_time = os.path.getmtime(path)

        if os.path.exists(cache):
            cache_time = os.path.getmtime(cache)
        else:
            # Cached image does not exist
            return False

        if original_time > cache_time:
            # Cached image is out of date
            return False
        else:
            return True
                
    def write(self, data):        
        path = self._cache_path()
        f = open(path, 'w')
        f.write(data)
        f.close()
    
    def read(self):
        f = open(self._cache_path(), "r")
        data = f.read()
        f.close()

        return data

class ImageModifier(object):
    """
    Modifies an image and saves to a cache location
    """
    
    """
    Output Formats:
    
    extension => ('format', 'mime-type')
    
    the key is the extension appended to the URL,
    the value tuple holds PIL's name for the format and the mime-type to serve
    with
    """
    output_formats = {
        'jpeg' : ('JPEG', 'image/jpeg'),               
        'jpg' : ('JPEG', 'image/jpeg'),
        'gif' : ('GIF', 'image/gif'),
        'png' : ('PNG', 'image/png'),
    }
    
    # When we process an image, these modifications are applied in order
    installed_modifications = (
        AutotrimMod,
        CropMod,
        ResizeMod,
    )
    
    quality = 80
    
    def __init__(self, url, config):
        self._url = url
        self._image_root = config['asset_root']
        self._process_path()
        
    def _process_path(self):
        """
        Extracts parameters from the image path
        
        Valid syntax:
        - /path/to/image.ext (serve image unchanged)
        - /path/to/image.ext.newext (change format of image)
        - /path/to/image.ext.options-string.newext (change format and modify
          image)
        
        Format of options string is:
        key1-value1_key2-value2_key3-value3
        """
        parts = self._url.split('.')
        
        length = len(parts)

        if length == 2:
            self.source_filename = self._url
            self._params = dict(type=parts[1])
        elif length == 3:
            self.source_filename = ".".join((parts[0],parts[1]))
            self._params = dict(type=parts[2])
        elif length == 4:
            self.source_filename = ".".join((parts[0],parts[1]))
            
            param_parts = parts[2].split('_')
            
            try:
                self._params = dict([(x.split("-")[0], x.split("-")[1]) for x in param_parts]) 
                self._params['type'] = parts[3]
            except IndexError, e:
                raise ResizerSyntaxException("Invalid filename syntax")
        else:
            raise ResizerSyntaxException("Invalid filename syntax")
        
        if self._params['type'] not in self.output_formats:
            raise ResizerFormatException("Invalid output format")     
    
    def source_path(self):
        return os.path.join(self._image_root,self.source_filename)
    
    def generate_image(self):
        source = Image.open(self.source_path())
        
        # Iterate over the installed modifications and apply them to the image
        for mod in self.installed_modifications:
            source = mod(source,self._params).apply()
            
        if (self._params['type'] == 'png'):
            source = source.convert("RGBA")
        else:
            source = source.convert("RGB")

        output = StringIO.StringIO()
        
        source.save(output, self.get_type()[0], quality=self.quality)
        
        output.seek(0)
        data = output.read()
        
        return data
    
    def get_type(self):
        return self.output_formats[self._params['type']]

class BaseImageHandler(object):
    """
    This can be called by a WSGI script, or via DjangoImageHandler.
    Django version is handy for local development, but adds unnecessary
    overhead to production
    """
    
    modifier = ImageModifier
    cache = DiskCache
    
    def build_response(self,data,modifier,start_response):
        """
        Serves the (now) cached image off the disc. It is assumed that the file
        actually exists as it's non-existence should have been picked up while
        checking to see if the cached version is valid.
        """
        status = '200 OK'
    
        response_headers = [('Content-type', modifier.get_type()[1]),
                            ('Content-Length', str(len(data)))]
        start_response(status, response_headers)
        
        return [data]
    
    def __call__(self,environ,start_response):
        path = environ.get('PATH_INFO')
        config = environ.get('MEDIA_CONFIG')
        
        # Don't bother processing stuff we know is invalid
        if path == '/' or path == '/favicon.ico':
            return error404(path, start_response)
        path = path[1:]

        try: 
            c = self.cache(path,config)
            m = self.modifier(path,config)
        except (ResizerSyntaxException, ResizerFormatException), e:
            return error500(path, e, start_response)
        try:
            if not c.check(m.source_path()):
                data = m.generate_image()
                c.write(data)
            return self.build_response(c.read(), m, start_response)
        except Exception, e:
            return error404(path, start_response)
    
class DjangoImageHandler(BaseImageHandler):
    
    def __call__(self, request):
        from django.http import HttpResponse
        from django.conf import settings
        
        environ = request.META.copy()

        environ['MEDIA_CONFIG'] = settings.DYNAMIC_MEDIA_CONFIG
        environ['PATH_INFO'] = environ['PATH_INFO'][len(settings.DYNAMIC_URL_PREFIX)+1:]

        django_response = HttpResponse()
        
        def start_response(status, headers):
            status, reason = status.split(' ', 1)
            django_response.status_code = int(status)
            for header, value in headers:
                django_response[header] = value
                
        response = super(DjangoImageHandler, self).__call__(environ, start_response)
        django_response.content = "\n".join(response)

        return django_response  