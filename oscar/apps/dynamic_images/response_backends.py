from oscar.apps.dynamic_images.exceptions import ResizerConfigurationError


class BaseResponse(object):
    def __init__(self,config,mime_type,cache,start_response):
        self.config = config
        self.mime_type = mime_type
        self.cache = cache
        self.start_response = start_response
        
    def build_response(self):
        pass


class DirectResponse(BaseResponse):
    """
    Serve the file directly, can use any caching mechanism
    """
    def build_response(self):
        """
        Serves the cached image directly.
        """
        status = '200 OK'

        data = self.cache.read()
        
        response_headers = [('Content-Type', self.mime_type),
                            ('Content-Length', str(len(data)))]
        self.start_response(status, response_headers)

        return [data]
    

class NginxSendfileResponse(BaseResponse):
    """
    This can only work with a disk-based caching system since it only returns
    headers about the file rather than the file data itself
    """
    
    def build_response(self):
        if not hasattr(self.cache, 'file_info'):
            msg = "Cache doesn't implements the method 'file_info'"
            raise ResizerConfigurationError(msg)
        if not self.config.get('nginx_sendfile_path',None):
            msg = 'Must provide nginx_sendfile_path in configuration'
            raise ResizerConfigurationError(msg)

        status = '200 OK'
        
        filename, content_length = self.cache.file_info()
        
        filename = self.config['nginx_sendfile_path'] + filename
        
        response_headers = [('Content-Type', self.mime_type),
                            ('Content-Length', content_length),
                            ('X-Accel-Redirect', filename)]
        
        self.start_response(status, response_headers)
        return ['']