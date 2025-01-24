from copy import deepcopy
from django.db import models
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.functional import cached_property


class QuerysetCache(dict):
    def __init__(self, queryset):
        self._queryset = queryset

        # It's possible the queryset is prefetched with prefetch_attribute_values.
        # In this case the queryset is actually a list, and thus we can't use .iterator(),
        if isinstance(queryset, list):
            self._queryset_iterator = queryset
        else:
            self._queryset_iterator = queryset.iterator()

    def queryset(self):
        return self._queryset

    def get(self, code, default=None):
        try:
            return self[code]
        except KeyError:
            for instance in self._queryset_iterator:
                instance_code = instance.code
                self[instance_code] = instance
                if instance_code == code:
                    return instance

        return default


class AttributesQuerysetCache:
    def __init__(self, product):
        self.product = product

    @cached_property
    def attributes(self):
        return QuerysetCache(self.product.get_product_class().attributes.all())

    @cached_property
    def attribute_values(self):
        # This means this product comes from a prefetched queryset with the
        # prefetch_attribute_values method. Which selects the attribute and
        # annotates the attribute code. This avoids the need of extra queries.
        if hasattr(self.product, "_prefetched_attribute_values"):
            return QuerysetCache(self.product.get_attribute_values())

        return QuerysetCache(
            self.product.get_attribute_values()
            .select_related("attribute")
            .annotate(code=models.F("attribute__code"))
        )

    def set_attributes(self, attributes):
        self.__dict__["attributes"] = attributes


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
        "prepare_save",
        "save",
        "set",
        "update",
        "validate_attributes",
    }

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

    def __getstate__(self):
        # Allow everything to go into the pickle except for _cache (which can't
        # be pickled since it contains a generator)
        d = {}
        d.update(self.__dict__)
        d["_cache"] = None
        return d

    def __setstate__(self, d):
        # Update __dict__ instead of setting it to avoid triggering __setattr__,
        # which causes a recursion error.
        self.__dict__.update(d)

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
                "%s is a reserved name and cannot be used as an attribute" % name
            )

        self._dirty.add(name)
        super().__setattr__(name, value)

    def set(self, name, value, validate_identifier=True):
        if not validate_identifier or name.isidentifier():
            self.__setattr__(name, value)
        else:
            raise ValidationError(
                _(
                    "%s is not a valid identifier, but attribute codes must be valid python identifiers"
                    % name
                )
            )

    def update(self, adict):
        self._dirty.update(adict.keys())
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

    def prepare_save(self):
        to_be_updated = []
        to_be_created = []
        to_be_deleted = []
        update_fields = set()

        if not self.initialized and not self._dirty:
            # no need to save untouched attr lists
            return (to_be_updated, to_be_created, to_be_deleted, update_fields)

        ProductAttributeValue = self.product.attribute_values.model

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
                        if (
                            attribute_value_current is not None
                            and attribute_value_current.value == value
                        ):
                            continue  # no new value needs to be saved
                    except ObjectDoesNotExist:
                        pass  # there is no existing value, so a value needs to be saved.

                if attribute.is_multi_option:  # multi_option can not be bulk saved
                    attribute.save_value(self.product, value)
                else:
                    value_obj = self.get_value_by_attribute(attribute)
                    if (
                        value_obj is None or value_obj.product != self.product
                    ):  # it doesn't exist yet so should be created
                        new_value_obj = ProductAttributeValue(
                            attribute=attribute, product=self.product
                        )

                        bound_value_obj = attribute.bind_value(new_value_obj, value)
                        # don't create attributevalues that wheren't even set at all.
                        if bound_value_obj is not None and bound_value_obj.is_dirty:
                            assert not bound_value_obj.pk
                            to_be_created.append(bound_value_obj)
                    else:
                        bound_value_obj = attribute.bind_value(value_obj, value)
                        if bound_value_obj is None:
                            to_be_deleted.append(value_obj.pk)
                        else:
                            if bound_value_obj.attribute.is_entity:
                                # entities can be bulk_created, but not bulk_saved
                                bound_value_obj.save()
                                continue

                            if bound_value_obj.attribute.is_file:
                                # with bulk_create the file is save just fine, but
                                # with buld_update, it's not, so we have to performa
                                # that manually
                                bound_value_obj._meta.get_field(
                                    bound_value_obj.value_field_name
                                ).pre_save(bound_value_obj, False)

                            to_be_updated.append(bound_value_obj)
                            update_fields.add(bound_value_obj.value_field_name)

        return (to_be_updated, to_be_created, to_be_deleted, update_fields)

    def save(self):
        to_be_updated, to_be_created, to_be_deleted, update_fields = self.prepare_save()

        # now save all the attributes in bulk
        if to_be_deleted:
            self.product.attribute_values.filter(pk__in=to_be_deleted).delete()
        if to_be_updated:
            self.product.attribute_values.bulk_update(
                to_be_updated, update_fields, batch_size=500
            )
        if to_be_created:
            self.product.attribute_values.bulk_create(
                to_be_created, batch_size=500, ignore_conflicts=False
            )

        # after this the current data is nolonger valid and should be refetched
        # from the database
        self.invalidate()
