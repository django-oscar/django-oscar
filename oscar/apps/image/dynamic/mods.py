import Image
import ImageChops
import math


def hex_to_color(hex):
    r = int(hex[0:2], 16)
    g = int(hex[2:4], 16)
    b = int(hex[4:6], 16)

    if len(hex) == 8:
        a = int(hex[6:8], 16)
    else:
        a = 255

    return (r, g, b, a)


class BaseModification(object):
    def __init__(self, image, params):
        self._params = params
        self._image = image

    def apply(self):
        pass


class AutotrimMod(BaseModification):
    def apply(self):
        keys = self._params.keys()
        if ('width' in keys or 'height' in keys) and not 'crop' in keys:
            if 'bgcolor' in keys:
                bgcolor = hex_to_color(self._params['bgcolor'])
            else:
                bgcolor = (255, 255, 255, 255)

            bg = Image.new(self._image.mode, self._image.size, bgcolor)
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
        keys = self._params.keys()
        if 'width' in keys or 'height' in keys:
            w = self._params.get('width', None)
            h = self._params.get('height', None)

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
                self._image = self._image.resize(new_size, Image.ANTIALIAS)

            new_w = int(target_w if target_w else self._image.size[0])
            new_h = int(target_h if target_h else self._image.size[1])

            if 'bgcolor' in keys:
                bgcolor = hex_to_color(self._params['bgcolor'])
            else:
                bgcolor = (255, 255, 255, 255)

            bg = Image.new(self._image.mode, (new_w, new_h), bgcolor)

            left = int(math.floor(float(new_w - self._image.size[0]) / 2))
            top = int(math.floor(float(new_h - self._image.size[1]) / 2))

            bg.paste(self._image, (left, top))

            return bg
        return self._image
