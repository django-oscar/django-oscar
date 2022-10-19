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
        self.product = product
        self.refresh()

    def refresh(self):
        values = self.get_values().select_related('attribute')
        for v in values:
            setattr(self, v.attribute.code, v.value)

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

                # only go and save values that have changed, don't do anything useless
                try:
                    attribute_value_current = self.get_value_by_attribute(attribute)
                    if attribute_value_current.value == value:
                        continue  # no new value needs to be saved
                except ObjectDoesNotExist:
                    pass  # there is no existing value, so a value needs to be saved.

                attribute.save_value(self.product, value)
