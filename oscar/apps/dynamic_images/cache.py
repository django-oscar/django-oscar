import os


class BaseCache(object):
    def __init__(self, path, config):
        self._path = path
        self._config = config

    def check(self, path):
        return False

    def write(self, data):
        pass

    def read(self):
        pass


class NullCache(BaseCache):
    """
    A dummy cache that doesn't do anything, handy for developing new Mods
    """
    def check(self, path):
        return False

    def write(self, data):
        self.data = data

    def read(self):
        return self.data


class DiskCache(BaseCache):
    """
    A simple disk-based cache.
    """
    def _create_folders(self):
        """
        Create the disk cache path so that the cached image can be stored in
        the same hierarchy as the original images.
        """
        paths = self._path.split(os.path.sep)
        paths.pop()  # Remove file from path
        path = os.path.join(self._config['cache_root'], *paths)

        if not os.path.isdir(path):
            os.makedirs(path)

    def _cache_path(self):
        return os.path.join(self._config['cache_root'], self._path)

    def check(self, path):
        """
        Checks the disk cache for an already processed image. If it exists then
        we'll check it's timestamp against the original image to make sure it's
        newer (and therefore valid). Also creates the folder hierarchy in the
        cache for the cached image if it doesn't find it there itself.
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
        
    def file_info(self):
        """
        If we're using X-Sendfile or X-Accel-Redirect we want to return info
        about the file, rather than the actual file content
        """
        size = os.path.getsize(self._cache_path())
        return (self._path, size)

    def read(self):
        f = open(self._cache_path(), "r")
        data = f.read()
        f.close()

        return data
