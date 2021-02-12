from django.conf import settings
from oscar.core.thumbnails import get_thumbnailer

default_SRCSETS = {
    'fullsizes': {
        'fullscreen': 1080,
        'tablet': 780,
        'mobile_large': 520,
        'moble_small': 280,
    },
    'thumbnails': {
        'large': 100,
        'small': 50,
    }
}
get_settings = lambda: getattr(settings,'OSCAR_SRCSETS', default_SRCSETS)

#tesed
def _get_srcset_sizes(srcsets=None, image_type=None):
        """Get sizes by any of the level 1 keys in the settings.SRCSETS dict."""
        srcsets = srcsets or get_settings()
        return ((image_type, k, v) for k,v in srcsets.get(image_type,{}).items()) if image_type \
            else ((k_2, k_1, v_1) for k_2, v_2 in srcsets.items() for k_1, v_1 in v_2.items())

#tested
def get_srcset_image(source, width, image_type=None, image_processor=None, do_upscale=False,
        settings=settings, **options):
        """Build and return the source set image objects."""

        # have to wrap sizes so they pass to thumbnailer as 'widthxheight'.
        # this is probably the worst part of the thumbnailers API.
        calc_img_dim = lambda source, width: f"{width}x{int((width / source.width) * source.height)}"
        
        # prevent upscaling by default.  Filter sizes out that are greater than the
        # uploaded source image.
        if not do_upscale and width >= source.width:
            return

        # give the options of passing in a custom image processor.
        image_processor = image_processor or get_thumbnailer().generate_thumbnail

        return image_processor(source, **dict({'size':calc_img_dim(source, width)},**options))
def get_srcset(source, image_type=None, image_processor=None, do_upscale=False,
        settings=settings, **options):
        gen_sizes = _get_srcset_sizes(get_settings(), image_type=image_type)
        gen_create_image = (
            (image_type, size, width, get_srcset_image(
                source, width, 
                image_type=image_type, 
                image_processor=image_processor, 
                do_upscale=do_upscale,
                settings=settings, 
                **options
            )) for image_type, size, width in gen_sizes)
        return (
            SrcsetImage(image, size, width, image_type) 
            for image_type, size, width, image in gen_create_image
            if image is not None
        )

class SrcsetImage():
    
    def __init__(self, image, size, width, image_type):
        self.image = image
        self.size = size
        self.width = width
        self.image_type = image_type
        return
    def __str__(self):
        return f'{image.url} {width}w'

class SrcsetCollection():
    
    def __init__(self, instance, srcset_images):
        self.instance = instance
        self._srcset = srcset_images
        return
    def __getattr__(self, name):
        rtn = next((si for si in self._srcset if si.size==name), None) \
            or [si for si in self._srcset if si.image_type==name]
        if rtn: 
            return rtn
        raise AttributeError()
    def __getitem__(self,name):
        return next((si for si in self._srcset if si.width==name), None) \
            or self.__getattr__(name)
    def __str__(self):
        return str(self._srcset)
    def __len__(self):
        return len(self._srcset)

class SrcSetDescriptor:

    def __init__(self, source_field, image_type=None, image_processor=None, do_upscale=False,
        settings=settings, **options):
        self.source_field = source_field
        self.image_type = image_type
        self.image_processor = image_processor or get_thumbnailer().generate_thumbnail
        self.do_upscale=do_upscale
        self.settings = settings or get_settings()
        self.options = options
        return

    def __get__(self, instance, cls=None):
        
        srcset = get_srcset(
            getattr(instance, self.source_field), 
                image_type=self.image_type, 
                image_processor=self.image_processor, 
                do_upscale=self.do_upscale,
                settings=self.settings, 
                **self.options
        )
        return SrcsetCollection(instance, list(srcset))
