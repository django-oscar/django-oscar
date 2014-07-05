from django.core.exceptions import ImproperlyConfigured
from django.db.models import base
from django.apps.registry import apps
from django.utils.six import add_metaclass


class ModelBase(base.ModelBase):
    def __new__(cls, name, bases, attrs):

        parents = [b for b in bases if isinstance(b, ModelBase)]
        new_class = super(base.ModelBase, cls).__new__(
            cls, name, bases, {'__module__': attrs['__module__']})

        if not parents:
            return new_class

        # Fetch the meta attribute
        attr_meta = attrs.get('Meta')
        if not attr_meta:
            meta = getattr(new_class, 'Meta', None)
        else:
            meta = attr_meta

        # Create the app_label and the model_name based on the meta
        app_label = meta.app_label if meta else 'oscar'
        model_name = name.lower()

        # If the model is already registered then return the existing one,
        # otherwise call the superclass.
        # Note that the migrations need to register an app twice, we allow
        # this for now then the module is '__fake__'. Seems a bit fragile but
        # works for now.
        app_models = apps.all_models[app_label]
        if model_name in app_models and new_class.__module__ != '__fake__':
            if not new_class.__module__.startswith('oscar.'):
                raise ImproperlyConfigured(
                    "Registered custom model %s.%s (%s) after Oscar's model" %
                    (app_label, model_name, new_class.__module__))
            return app_models[model_name]
        return super(ModelBase, cls).__new__(cls, name, bases, attrs)


@add_metaclass(ModelBase)
class Model(base.Model):
    pass
