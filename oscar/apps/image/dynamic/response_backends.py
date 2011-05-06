from oscar.apps.image.dynamic.exceptions import ResizerConfigurationException

class BaseResponse(object):
    def __init__(self,mime_type,cache,start_response):
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
        Serves the (now) cached image off the disc. It is assumed that the file
        actually exists as it's non-existence should have been picked up while
        checking to see if the cached version is valid.
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
            raise ResizerConfigurationException(msg)

        print 'moooo'
        
        status = '200 OK'
        
        filename, content_length = self.cache.file_info()
        
        response_headers = [('Content-Type', self.mime_type),
                            ('Content-Length', content_length),
                            ('X-Accel-Redirect', filename)]
        
        self.start_response(status, response_headers)
        return ['']
    
class ApacheSendfileResponse(BaseResponse):
    def build_response(self):
        if not hasattr(self.cache, 'file_info'):
            msg = "ApacheSendfileResponse requires a cache that implements the method 'file_data'"
            raise ResizerConfigurationException(msg)
        
        status = '200 OK'
        
        filename, content_length = self.cache.file_info()
        
        response_headers = [('Content-Type', self.mime_type),
                            ('Content-Length', content_length),
                            ('X-Sendfile', filename)]
        
        self.start_response(status, response_headers)
        return ['']
