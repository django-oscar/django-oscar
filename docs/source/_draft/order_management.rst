Order management REST services
==============================

Supported methods and resources:

**Retrieve list of orders:**::

    GET /orders/

Filters:

* ``after=2010-10-01`` - Return all orders placed after 2010-10-01
* ``before=2010-10-31`` - Return all orders placed before 2010-10-31

**Retrieve a summary of an order with number 123 (not id)**::

    GET /order/123/

**Retrieve a list of batches**::

    GET /order/123/batches/

**Retrieve a summary of batch**::

    GET /order/123/batch/34/

**Retrieve a list of lines**::

    GET /order/123/batch/34/lines/ [just lines within batch 34, part of order 123]
    
    GET /order/123/lines/ [all lines within order 123]
    
    GET /lines/ [all lines]

Filters:

* ``at_shipping_status`` - Returns lines at the specified shipping status (use the code)

* ``at_payment_status`` - Returns lines at the specified payment status (use the code)

* ``partner`` - Returns lines fulfilled by a particular partner

**Retrieve a summary of a lines with ids 100,101,102**::

    GET /order/123/batch/34/line/100;101;102`` 

    GET /order/123/line/100;101;102`` 

**Update shipping status of an order line**::

    POST /order/123/batch/34/line/100/ 

    POST /order/123/lines/ 

Request:

``{'shipping_status': 'acknowledged'}`` - Update every item in line

``{'shipping_status': {'acknowledged': 10, 'cancelled': 1}}`` - Fine-grained control



