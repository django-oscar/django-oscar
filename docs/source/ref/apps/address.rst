=======
Address
=======

The address app provides core address models - it doesn't provide any views or
other functionality.  Of the 5 abstract models, only 2 have a non-abstract
version in ``oscar.apps.address.models`` - the others are used by the order app
to provide shipping and billing address models.

Abstract models
---------------

.. autoclass:: oscar.apps.address.abstract_models.AbstractAddress
    :members:
    :show-inheritance:

.. autoclass:: oscar.apps.address.abstract_models.AbstractShippingAddress
    :members:
    :show-inheritance:

.. autoclass:: oscar.apps.address.abstract_models.AbstractUserAddress
    :members:
    :show-inheritance:

.. autoclass:: oscar.apps.address.abstract_models.AbstractBillingAddress
    :members:
    :show-inheritance:

.. autoclass:: oscar.apps.address.abstract_models.AbstractCountry
    :members:
    :show-inheritance:
