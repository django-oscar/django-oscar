========================
How to create categories
========================

The simplest way is to use a string which represents the breadcrumbs::

    from oscar.apps.catalogue.categories import create_from_breadcrumbs

    categories = (
        'Food > Cheese',
        'Food > Meat',
        'Clothes > Man > Jackets',
        'Clothes > Woman > Skirts',
    )
    for breadcrumbs in categories:
        create_from_breadcrumbs(breadcrumbs)

