from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _


class ProductAttributesContainer:
    """
    Stolen liberally from django-eav, but simplified to be product-specific

    To set attributes on a product, use the `attr` attribute:

        product.attr.weight = 125

    To refetch the attribute values from the database:

        product.attr.refresh()
    """

    def __setstate__(self, state):
        self.__dict__ = state

    def __init__(self, product):
        self._product = product
        self._initialized = False

    @property
    def product(self):
        return self._product

    def initialize(self):
        self._initialized = True
        # initialize should not overwrite any values that have allready been set
        attrs = self.__dict__
        for v in self.get_values().select_related('attribute'):
            attrs.setdefault(v.attribute.code, v.value)

    def refresh(self):
        for v in self.get_values().select_related('attribute'):
            setattr(self, v.attribute.code, v.value)

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            if self._initialized:
                raise
            else:
                self.initialize()
                # try again, whever happens then will just be the result.
                return super().__getattribute__(name)

    def __getattr__(self, name):
        raise AttributeError(
            _("%(obj)s has no attribute named '%(attr)s'") % {'obj': self.product.get_product_class(), 'attr': name})

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
        return self.product.get_attribute_values()

    def get_value_by_attribute(self, attribute):
        return self.get_values().get(attribute=attribute)

    def get_all_attributes(self):
        return self.product.get_product_class().attributes.all()

    def get_attribute_by_code(self, code):
        return self.get_all_attributes().get(code=code)

    def __iter__(self):
        return iter(self.get_values())

    def save(self):
        for attribute in self.get_all_attributes():
            if hasattr(self, attribute.code):
                value = getattr(self, attribute.code)
                # Make sure that if a value comes from a parent product, it is not
                # copied to the child, we do this by checking if a value has been
                # changed, which would not be the case if the value comes from the
                # parent.
                try:
                    attribute_value_current = self.get_value_by_attribute(attribute)
                    if attribute_value_current.value == value:
                        continue  # no new value needs to be saved
                except ObjectDoesNotExist:
                    pass  # there is no existing value, so a value needs to be saved.

                attribute.save_value(self.product, value)
