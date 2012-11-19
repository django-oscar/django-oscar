========
Checkout
========

Flow
----

The checkout process comprises the following steps:

1.  **Gateway** - For anonymous users, they are offered the choice of logging in, registering
    or checking out anonymously.  Signed in users will be automatically redirected to the next
    step.

2.  **Shipping address** - Enter or choose a shipping address.

3.  **Shipping method** - Choose a shipping method.  If only one shipping method is available
    then it is automatically chosen and the user is redirected onto the next step.  

4.  **Payment method** - Choose the method of payment plus any allocations if payment is to be
    split across multiple sources.  If only one method is available, then the user is
    redirected onto the next step.

5.  **Preview** - The prospective order can be previewed.

6.  **Payment details** - If any sensitive payment details are required (eg bankcard number), 
    then a form is presented within this step.  This has to be the last step before submission
    so that sensitive details don't have to be stored in the session.

7.  **Submission** - The order is placed.

8.  **Thank you** - A summary of the order with any relevant tracking information.


Customisation
-------------

The checkout can be customised in many ways as you can extend and override and class from
Oscar's core using the overriding core classes technique detailed previously.
