from django.db import models

class AttributeType(models.Model):
    """Defines a product atrribute type"""
    name = models.CharField(max_length = 128)

    def __unicode__(self):
        return self.name


class Type(models.Model):
    """Defines a product type"""
    name = models.CharField(max_length = 128)
    attribute_types = models.ManyToManyField('product.AttributeType')

    def __unicode__(self):
        return self.name

class Item(models.Model):
    """The base product object"""
    name = models.CharField(max_length = 128)
    partner_id = models.CharField(max_length = 32)
    type = models.ForeignKey('product.Type')
    date_available = models.DateField()
    date_created = models.DateTimeField()

    def __unicode__(self):
        return self.name

    def is_valid(self):
        """
        Returns true if the product is valid.

        Validity is based on whether the product has all required attribute types
        configured for the product_class it is in.

        Returns:
            A boolean if the product is valid
        """
        required_attribute_names = []
        for attribute_type in self.type.attribute_types.all():
            required_attribute_names.append(attribute_type.name)

        for attribute in self.attribute_set.all():
            required_attribute_names.remove(attribute.attribute_type.name)

        return 0 == len(required_attribute_names)

class Attribute(models.Model):
    """An individual product attribute"""
    attribute_type = models.ForeignKey('product.AttributeType')
    product = models.ForeignKey('product.Item')
    value = models.CharField(max_length = 256)


class StockRecord(models.Model):
    """A stock keeping record"""
    product = models.ForeignKey('product.Item')
    price_excl_tax = models.FloatField()
    tax = models.FloatField()
