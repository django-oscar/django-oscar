================================
How to configure stock messaging
================================

Stock messaging is controlled by an
:ref:`availability policy <availability_policies>`
which is loaded by the :ref:`strategy class <strategy_class>`.

To set custom availability messaging, use your own strategy class to return the
appropriate availability policy.  It's possible to return different availability
policies depending on the user, request and product in question.
