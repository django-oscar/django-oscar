from copy import deepcopy
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class QuerysetCache(dict):
    def __init__(self, queryset, key_func):
        self._key_func = key_func
        self._queryset = queryset
        self._queryset_iterator = queryset.iterator()

    def queryset(self):
        return self._queryset

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            for instance in self._queryset_iterator:
                instance_key = self._key_func(instance)
                self[instance_key] = instance
                if instance_key == key:
                    return instance

        return default


class AttributesQuerysetCache:
    def __init__(self, product):
        self.product = product

    @cached_property
    def attributes(self):
        return QuerysetCache(
            self.product.get_product_class().attributes.all(), lambda a: a.code
        )

    @cached_property
    def attribute_values(self):
        return QuerysetCache(
            self.product.get_attribute_values().select_related("attribute"),
            lambda v: v.attribute.code,
        )


class ProductAttributesContainer:
    """
    Stolen liberally from django-eav, but simplified to be product-specific

    To set attributes on a product, use the `attr` attribute:

        product.attr.weight = 125

    To refetch the attribute values from the database:

        product.attr.refresh()
    """

    RESERVED_ATTRIBUTES = {
        "_cache",
        "_dirty",
        "initialized",
        "_initialized",
        "_product",
        "get_all_attributes",
        "get_attribute_by_code",
        "get_value_by_attribute",
        "get_values",
        "initialize",
        "product",
        "refresh",
        "save",
        "set",
        "update",
        "validate_attributes",
    }

    # pylint: disable=access-member-before-definition
    def __setstate__(self, state):
        self.__dict__.setdefault("_product", None)
        self.__dict__.setdefault("_initialized", False)
        self.__dict__.setdefault("_dirty", set())
        self.__dict__.setdefault("_cache", {})
        self.__dict__ = state

    def __init__(self, product):
        # use __dict__ directly to avoid triggering __setattr__, which would
        # cause a recursion error on _initialized.
        self.__dict__.update(
            {
                "_product": product,
                "_initialized": False,
                "_dirty": set(),
                "_cache": None,
            }
        )

    def __deepcopy__(self, memo):
        cpy = ProductAttributesContainer(self.product)
        memo[id(self)] = cpy
        if self.initialized:
            # Only copy attributes for initialized containers
            for key, value in self.__dict__.items():
                if key != "_cache":
                    cpy.__dict__[key] = deepcopy(value, memo)

        return cpy

    @property
    def product(self):
        return self._product

    @property
    def initialized(self):
        return self._initialized

    @property
    def cache(self):
        if self.__dict__["_cache"] is None:
            self.__dict__["_cache"] = AttributesQuerysetCache(self.product)
        return self.__dict__["_cache"]

    def initialize(self):
        self.__dict__["_initialized"] = True
        # initialize should not overwrite any values that have allready been set
        attrs = self.__dict__
        for v in self.get_values():
            attrs.setdefault(v.attribute.code, v.value)

    def invalidate(self):
        "Invalidate any stored data, queried from the database"
        self.__dict__["_cache"] = None
        self.__dict__["_initialized"] = False

    def refresh(self):
        "Reload any queried data from the database, discarding local changes"
        self.__dict__["_cache"] = None
        for v in self.get_values():
            setattr(self, v.attribute.code, v.value)

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            if self.initialized:
                raise
            else:
                self.initialize()
                # try again, whever happens then will just be the result.
                return super().__getattribute__(name)

    def __getattr__(self, name):
        raise AttributeError(
            _("%(obj)s has no attribute named '%(attr)s'")
            % {"obj": self.product.get_product_class(), "attr": name}
        )

    def __setattr__(self, name, value):
        if name in self.RESERVED_ATTRIBUTES:
            raise ValidationError(
                "%s is a reserved name and cannot be used as an attribute"
            )

        self._dirty.add(name)
        super().__setattr__(name, value)

    def set(self, name, value):
        if name.isidentifier():
            self.__setattr__(name, value)
        else:
            raise ValidationError(
                _(
                    "%s is not a valid identifier, but attribute codes must be valid python identifiers"
                )
            )

    def update(self, adict):
        self._dirty.extend(adict.keys())
        self.__dict__.update(adict)

    def validate_attributes(self):
        for attribute in self.get_all_attributes():
            value = getattr(self, attribute.code, None)
            if value is None:
                if attribute.required:
                    raise ValidationError(
                        _("%(attr)s attribute cannot be blank")
                        % {"attr": attribute.code}
                    )
            else:
                try:
                    attribute.validate_value(value)
                except ValidationError as e:
                    raise ValidationError(
                        _("%(attr)s attribute %(err)s")
                        % {"attr": attribute.code, "err": e}
                    )

    def get_values(self):
        return self.cache.attribute_values.queryset()

    def get_value_by_attribute(self, attribute):
        return self.cache.attribute_values.get(attribute.code)

    def get_all_attributes(self):
        return self.cache.attributes.queryset()

    def get_attribute_by_code(self, code):
        return self.cache.attributes.get(code)

    def __iter__(self):
        return iter(self.get_values())

    def save(self):
        if not self.initialized and not self._dirty:
            return  # no need to save untouched attr lists

        for attribute in self.get_all_attributes():
            if hasattr(self, attribute.code):
                value = getattr(self, attribute.code)
                if attribute.code not in self._dirty:
                    # Make sure that if a value comes from a parent product, it is not
                    # copied to the child, we do this by checking if a value has been
                    # changed, which would not be the case if the value comes from the
                    # parent.
                    # for attributes are are set explicitly (_dirty), this check is not
                    # needed and should always be saved.
                    try:
                        attribute_value_current = self.get_value_by_attribute(attribute)
                        if attribute_value_current.value == value:
                            continue  # no new value needs to be saved
                    except ObjectDoesNotExist:
                        pass  # there is no existing value, so a value needs to be saved.

                attribute.save_value(self.product, value)
