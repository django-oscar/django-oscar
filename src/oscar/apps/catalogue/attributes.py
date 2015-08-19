from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


class ProductAttributesContainer(object):
    """
    Stolen liberally from django-eav, but simplified to be product-specific

    To set attributes on a product, use the `attr` attribute:

        product.attr.weight = 125
    """

    def __setstate__(self, state):
        self.__dict__ = state
        self.initialised = False

    def __init__(self, product):
        self.product = product
        self.initialised = False

    def __getattr__(self, name):
        if not name.startswith('_') and not self.initialised:
            self._load_values()
            return getattr(self, name)
        raise AttributeError(
            _("%(obj)s has no attribute named '%(attr)s'") % {
                'obj': self.product.get_product_class(), 'attr': name})

    def validate_attributes(self):
        for attribute in self.get_all_attributes():
            value = getattr(self, attribute.code, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(
                        _("%(attr)s attribute cannot be blank") %
                        {'attr': attribute.code})
            else:
                try:
                    attribute.validate_value(value)
                except ValidationError as e:
                    raise ValidationError(
                        _("%(attr)s attribute %(err)s") %
                        {'attr': attribute.code, 'err': e})

    def get_values(self):
        return self.product.attribute_values.all()

    def get_value_by_attribute(self, attribute):
        return self.get_values().get(attribute=attribute)

    def get_all_attributes(self):
        return self.product.get_product_class().attributes.all()

    def get_attribute_by_code(self, code):
        return self.get_all_attributes().get(code=code)

    def __iter__(self):
        return iter(self.get_values())

    def refresh_from_db(self):
        self._load_values()

    def save(self):
        if not hasattr(self, '_initial_state'):
            self._initial_state = {}

        dirty_attributes = [
            attr for attr in self.get_all_attributes()
            if getattr(self, attr.code) != self._initial_state.get(attr.code)
        ]
        if not dirty_attributes:
            return

        # We don't filter on the attributes here since we assume all objects
        # are still available in the orm cache.
        value_objects = {v.attribute_id: v for v in self.get_values()}
        for attribute in dirty_attributes:
            new_value = getattr(self, attribute.code)
            value_obj = value_objects.get(attribute.pk)

            # Manually set the reverse relation instead of letting
            # Django fetch it again.
            if value_obj:
                value_obj.attribute = attribute
            attribute.save_value(self.product, new_value, value_obj)

    def _load_values(self):
        values = {v.attribute_id: v for v in self.get_values()}
        attrs = self.product.get_product_class().attributes.all()

        self._initial_state = {}
        for attr in attrs:
            value = values.get(attr.pk)
            value = value.value if value else None
            setattr(self, attr.code, value)
            self._initial_state[attr.code] = value

        self.initialised = True
