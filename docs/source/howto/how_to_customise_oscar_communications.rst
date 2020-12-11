Customising Oscar's communications
==================================

Oscar provides the ability to customise the emails sent out to customers.

There are two main ways this can be achieved, either in code (via template
files) or in the database (via Dashboard > Content > Email templates).

Communications API
------------------

First, it's important to understand a little about how the Communications API
works.

Oscar has a model called a ``CommunicationEventType``.  When preparing an email
to send out to a customer, the client code will do something like this::

    commtype_code = 'SOME_EVENT'
    context = {'customer': customer, 'something_else': 'Some more context.'}

    try:
        event_type = CommunicationEventType.objects.get(code=commtype_code)
    except CommunicationEventType.DoesNotExist:
        messages = CommunicationEventType.objects.get_and_render(commtype_code, ctx)
    else:
        messages = event_type.get_messages(ctx)

What's happening here is:

- The code defines an arbitrary communication type code to be treated as the
  reference for this particular type of communication.  For example, the
  communication type code used when sending an order email confirmation is
  ``'ORDER_PLACED'``.
- The database is checked for a ``CommunicationEventType`` with this
  communication type code.  If it does, it renders the messages using that model
  instance, passing in some context.
- Otherwise, it uses the ``get_and_render()`` method to render the messages,
  which uses templates instead.

So, your first step when customising the emails sent out is to work out what
communication type code is being used to send out the email. The easiest way to
work this out is usually to look through  the email templates in
:file:`templates/oscar/communication/emails`: if the email template is called, say,
:file:`commtype_order_placed_body.html`, then the code will be ``'ORDER_PLACED'``.
See 'Customising through code' below.

Customising through code
------------------------

Customising emails through code uses Django's standard template inheritance.

The first step is to locate the template for the particular email, which is
usually in :file:`templates/oscar/communication/emails`.  Then, in a template directory that
takes precedence over the oscar templates directory, copy the file and customise
it.  For example, to override the
:file:`templates/oscar/communication/emails/commtype_order_placed_body.html` template,
create :file:`oscar/communication/emails/commtype_order_placed_body.html` in your
template directory.

Note that usually emails have three template files associated with them: the
email subject line (:file:`commtype_{CODE}_subject.txt`), the html version
(:file:`commtype_{CODE}_body.html`) and the text version (:file:`commtype_{CODE}_body.txt`).
Usually you will want to make sure you override BOTH the html and the text
version.

Customising through code will not work if there is a template defined in the
database instead (see below).


Customising through the database
--------------------------------

Oscar provides a dashboard interface to allow admins to customise the emails.

To enable this for a particular communication event type, log in to the admin
site and create a new ``CommunicationEventType``.  The code you use is the
important thing: it needs to match the communication event code used when
rendering the messages.  For example, to override the order confirmation email,
you need to create a ``CommunicationEventType`` with a code ``'ORDER_PLACED'``.

Once you have created the ``CommunicationEventType``, you can edit it using the
(much better) dashboard interface at Dashboard > Content > Email templates.

If you have an email template defined in the database it will override any
template files.
