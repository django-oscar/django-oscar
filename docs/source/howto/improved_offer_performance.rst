Product Category Materialized View
==================================

Overview
--------

To improve performance in Oscar projects with complex category hierarchies,
a PostgreSQL materialized view named ``catalogue_product_category_hierarchy`` has been introduced.

This view precomputes the full ancestry relationship between products and their
associated categories (including all parent categories), which significantly speeds up
offer conditions and product range filtering.

Activation Requirements
-----------------------

This feature is **opt-in** and requires the following:

1. **PostgreSQL** as the database backend (materialized views are PostgreSQL-specific).
2. Set the following in your settings:

   .. code-block:: python

       OSCAR_CATALOGUE_USE_POSTGRES_MATERIALISED_VIEWS = True

If either of these conditions is not met, Oscar will fall back to the default behavior.

Motivation
----------

Oscar allows deep category trees, but products are often linked only to leaf categories.
To find all products under a given category (including its descendants), traditional queries
must recursively traverse the tree, which becomes slow with large datasets.

This materialized view eliminates those expensive lookups by flattening and caching
product-to-category (and ancestor) relationships.

Benefits for Custom Assortments
-------------------------------

With this flattened structure, implementing **user-specific assortments** or **custom category trees**
is more straightforward. You can easily filter product access or visibility based on category IDs.

For example, if certain users or tenants should only see a specific subset of categories or products,
you can use this view to efficiently filter the catalog by their allowed category IDs.

This approach scales better than traversing the category tree on every request.

Schema
------

The materialized view contains the following fields:

- ``id``: A unique identifier composed of ``product_id`` and ``category_id``.
- ``product_id``: FK to ``catalogue_product``.
- ``category_id``: FK to ``catalogue_category``

Each product is linked not only to its direct category but also to all of its ancestor categories.

SQL Definition
--------------

The materialized view is defined with the following SQL:

.. code-block:: sql

    CREATE MATERIALIZED VIEW IF NOT EXISTS catalogue_product_category_hierarchy AS
    WITH RECURSIVE category_hierarchy AS (
        SELECT id, path FROM catalogue_category
    )
    SELECT DISTINCT 
        CONCAT(p.id, '-', parent_categories.id) AS id,
        p.id AS product_id, 
        parent_categories.id AS category_id
    FROM catalogue_productcategory pc
    JOIN catalogue_category child_categories ON pc.category_id = child_categories.id
    JOIN catalogue_category parent_categories 
        ON child_categories.path LIKE parent_categories.path || '%'
    JOIN catalogue_product p ON p.id = pc.product_id;

And the index:

.. code-block:: sql

    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS catalogue_product_category_hierarchy_idx 
    ON catalogue_product_category_hierarchy (product_id, category_id);

Automatic Refresh via Signal
----------------------------

By default, Oscar connects a signal that **automatically refreshes** the materialized view
whenever product-category relationships or categories change.

This ensures the view stays up-to-date in real time, without requiring manual refresh.

Manual Refresh for Large Sites
------------------------------

On very large sites, automatic refreshes after every change can be expensive.

You may choose to **unregister the signal** and refresh the view manually,
for example after a nightly product/category sync:

.. code-block:: python

    from oscar.apps.catalogue.signals import product_category_view_refresher
    from django.db.models.signals import post_save, post_delete

    # Disconnect the automatic refresher
    post_save.disconnect(product_category_view_refresher)
    post_delete.disconnect(product_category_view_refresher)

Then, you can refresh the view manually as needed:

.. code-block:: sql

    REFRESH MATERIALIZED VIEW CONCURRENTLY catalogue_product_category_hierarchy;

This gives you full control over performance in high-volume environments.

Migration Example
-----------------

The view and its index are created via a Django migration:

.. code-block:: python

    from django.db import migrations, connection
    from oscar.checks import is_postgres

    def create_materialized_view(apps, schema_editor):
        if is_postgres():
            with connection.cursor() as cursor:
                cursor.execute("""
                    CREATE MATERIALIZED VIEW IF NOT EXISTS catalogue_product_category_hierarchy AS
                    WITH RECURSIVE category_hierarchy AS (
                        SELECT id, path FROM catalogue_category
                    )
                    SELECT DISTINCT 
                        CONCAT(p.id, '-', parent_categories.id) AS id,
                        p.id AS product_id, 
                        parent_categories.id AS category_id
                    FROM catalogue_productcategory pc
                    JOIN catalogue_category child_categories ON pc.category_id = child_categories.id
                    JOIN catalogue_category parent_categories 
                        ON child_categories.path LIKE parent_categories.path || '%'
                    JOIN catalogue_product p ON p.id = pc.product_id;
                """)
                cursor.execute("""
                    CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS catalogue_product_category_hierarchy_idx 
                    ON catalogue_product_category_hierarchy (product_id, category_id);
                """)

    def drop_materialized_view(apps, schema_editor):
        if is_postgres():
            with connection.cursor() as cursor:
                cursor.execute("DROP MATERIALIZED VIEW IF EXISTS catalogue_product_category_hierarchy;")
                cursor.execute("DROP INDEX IF EXISTS catalogue_product_category_hierarchy_idx;")

    class Migration(migrations.Migration):
        atomic = False
        dependencies = [
            ("catalogue", "0029_product_code"),
        ]
        operations = [
            migrations.RunPython(create_materialized_view, drop_materialized_view),
        ]

Usage
-----

To retrieve all products in a category and its subcategories using Django's ORM,
query the materialized view model, which maps to the PostgreSQL view:

.. code-block:: python

    from oscar.core.loading import get_model

    Product = get_model("catalogue", "Product")
    ProductCategoryHierarchy = get_model("catalogue", "ProductCategoryHierarchy")

    category_id = 123  # Replace with your target category's ID

    product_ids = ProductCategoryHierarchy.objects.filter(
        category_id=category_id
    ).values_list("product_id", flat=True)

    products = Product.objects.filter(id__in=product_ids)

This will return all products that are directly or indirectly associated with
the target category, thanks to the precomputed ancestor relationships in the view.

Reference
---------

- Pull request: https://github.com/django-oscar/django-oscar/pull/4436
