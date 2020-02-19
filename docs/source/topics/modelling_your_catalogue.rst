========================
Modelling your catalogue
========================

Oscar gives you several layers of modelling your products.

Note that this document is merely concerned with how to model products in your
database. How you display them in your front-end, e.g. in a category tree,
is out of scope.

Product classes
---------------

Typical examples for product classes would be: T-shirts, Books,
Downloadable products.

Each product is assigned to exactly one product class.

Settings on a product class decide whether stock levels are
:attr:`tracked <oscar.apps.catalogue.abstract_models.AbstractProductClass.track_stock>`
for the associated products, and whether they
:attr:`require shipping <oscar.apps.catalogue.abstract_models.AbstractProductClass.requires_shipping>`.

Furthermore, they govern what kind of product attributes can be stored on the products.
We'll get to attributes in a bit, but think T-shirt sizes, colour,
number of pages, etc.

Typically stores will have between 1 and maybe 5 product classes.

Product attributes
------------------

Product attributes let you set additional data on a product without having
to customise the underlying Django models. There's different types of
attributes, e.g. ones for just associating text (type ``text`` or ``richtext``),
for related images and files (type ``image`` and ``file``), etc.

Storing data in structured attributes also makes it easy to search and filter
products based on specific attributes.

The available product attributes for a product are set when creating the
product's class. The sandbox comes with a product class for T-shirts, and
they have a ``size`` attribute::

    > shirt = Product.objects.filter(product_class__slug='t-shirt').first()
    > shirt.attr.size
    <AttributeOption: Large>

You can assign ``option`` s to your product. For example you want a Language attribute
to your product, and a couple of options to choose from, for example English and
Croatian. You'd first create an ``AttributeOptionGroup`` that would contain all the
``AttributeOption`` s you want to have available::

    > language = AttributeOptionGroup.objects.create(name='Language')

Assign a couple of options to the Language options group::

    > AttributeOption.objects.create(
    >     group=language,
    >     option='English'
    > )
    > AttributeOption.objects.create(
    >     group=language,
    >     option='Croatian'
    > )

Finally assign the Language options group to your product as an attribute::

    > klass = ProductClass.objects.create(name='foo', slug='bar')
    > ProductAttribute.objects.create(
    >     product_class=klass,
    >     name='Language',
    >     code='language',
    >     type='option',
    >     option_group=language
    > )

You can go as far as associating arbitrary models with it. Use the ``entity``
type::

    > klass = ProductClass.objects.create(name='foo', slug='bar')
    > ProductAttribute.objects.create(
          product_class=klass, name='admin user', code='admin_user', type='entity')
    <ProductAttribute: admin user>
    > p = Product(product_class=klass)

    > p.attr.admin_user = User.objects.first()
    > p.save()
    > p.attr.admin_user
    <User: superuser>

You can also use the ``multi_option`` attribute type if your options are not
mutually exclusive::

    > klass = ProductClass.objects.create(name='foo', slug='bar')
    > ProductAttribute.objects.create(
    >     product_class=klass,
    >     name='Size',
    >     code='size',
    >     type='multi_option',
    >     option_group=language
    > )

This will let you assign multiple values (``size`` in the example above) to the
attribute.

You can also query for attributes using a special method on the manager::

    > first_large_shirt = Product.objects.filter_by_attributes(size="Large").first()
    > first_large_shirt.attr.size
    <AttributeOption: Large>

All attribute types apart from ``entity`` can be edited in the product
dashboard. The latter is too dependent on your use case and you will need to
decide yourself how you want to set and display it.

Variants (Parent and child products)
------------------------------------

Often there's an overarching product, which groups other products. In that
case, you can create a parent product, and then set the ``parent`` field on the
child products. By default, only parent products (or products without children)
get their own URL.
Child products inherit their product class from the parent, and only child
products can have stock records (read: pricing information) on them.

Product attributes vs. variants
-------------------------------

When to use variants, and when to use attributes?

- Variants are tied to stock records, and hence, pricing.
  Use variants if your product variations have different pricing or availability.

- Use attributes when you are storing structured data for a product (i.e. colour, size)
  that you can use for search/filtering/display purposes.

Going further
-------------

Oscar's modelling options don't stop there. If the existing framework does not
suit your need, you can always :doc:`customise </howto/how_to_customise_models>`
any involved models. E.g. the ``Product`` model is often customised!
