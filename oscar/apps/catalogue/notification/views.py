from django.conf import settings
from django.views import generic
from django.http import HttpResponseRedirect, Http404

from django.core import mail
from django.contrib import messages
from django.db.models import get_model
from django.template import loader, Context
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from oscar.apps.catalogue.notification.forms import ProductNotificationForm

Product = get_model('catalogue', 'product')
ProductNotification = get_model('notification', 'productnotification')


class NotificationUnsubscribeView(generic.RedirectView):
    """
    View to unsubscribe from a notification based on the provided
    unsubscribe key. The notification is set to ``INACTIVE`` instead
    of being deleted for analytical purposes.
    """
    model = ProductNotification
    context_object_name = 'notification'

    def get_object(self, queryset=None):
        """ Get notification object that matches the unsubscribe key. """
        try:
            return self.model.objects.get(
                unsubscribe_key=self.kwargs.get('key', 'invalid')
            )
        except self.model.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        notification = self.get_object()
        notification.status = ProductNotification.INACTIVE
        notification.save()
        messages.info(self.request,
            _("You have successfully unsubscribed from this notification.")
        )
        kwargs['notification'] = notification
        return super(NotificationUnsubscribeView, self).get(*args, **kwargs)

    def get_redirect_url(self, **kwargs):
        return kwargs.get('notification').get_absolute_item_url()


class NotificationConfirmView(generic.RedirectView):
    """
    View to confirm the email address of an anonymous user used to
    sign up for a product notification.
    """
    model = ProductNotification
    context_object_name = 'notification'

    def get_object(self, queryset=None):
        """ Get notification object that matches the confirmation key. """
        try:
            return self.model.objects.get(
                confirm_key=self.kwargs.get('key', 'invalid')
            )
        except self.model.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        notification = self.get_object()
        notification.status = self.model.ACTIVE
        notification.save()
        messages.info(self.request,
            _("Yeah! You have confirmed your subscription. We'll notify "
              "you as soon as the product is back in stock.")
        )
        kwargs['notification'] = notification
        return super(NotificationConfirmView, self).get(*args, **kwargs)

    def get_redirect_url(self, **kwargs):
        return kwargs.get('notification').get_absolute_item_url()


class ProductNotificationCreateView(generic.FormView):
    """
    View to create a new product notification based on a registered user
    or an email address provided by an anonymous user.
    """
    product_model = Product
    form_class = ProductNotificationForm
    template_name = 'notification/notification.html'
    email_template = 'notification/email.html'

    def get_form_kwargs(self):
        """
        Get keywords to instantiate the view's form with. If the current
        user is authenticated as registered user, their email address is
        added to the ``initial`` dictionary as ``email`` which prepopulates
        the ``email`` form field.
        """
        kwargs = super(ProductNotificationCreateView, self).get_form_kwargs()

        user = self.request.user
        if user.is_authenticated():
            kwargs['initial'].update({'email': user.email})
        return kwargs

    def get_product(self):
        """
        Get product from primary key specified in URL patterns as
        ``pk``. Raises a 404 if product does not exist.
        """
        return get_object_or_404(self.product_model, pk=self.kwargs['pk'])

    def get_context_data(self, *args, **kwargs):
        """
        Get context data including ``product`` representing the product
        related to this product notification.
        """
        ctx = super(ProductNotificationCreateView, self).get_context_data(
            *args,
            **kwargs
        )
        ctx['product'] = self.get_product()
        return ctx

    def get_notification_for_anonymous_user(self, email):
        """
        Get a the ``ProductNotification`` for the given product and anonymous
        users email address. If no notification exists, a new
        ``ProductNotification`` will be created for the product. A newly
        created ``ProductNotification`` will be set to status ``UNCONFIRMED``
        and need confirmation of the email address.
        """
        notification, created = ProductNotification.objects.get_or_create(
            email=email,
            product=self.product,
        )

        if created:
            notification.status = ProductNotification.UNCONFIRMED
            notification.save()
        return notification, created

    def get_notification_for_authenticated_user(self):
        """
        Get a the ``ProductNotification`` for the given product and anonymous
        users email address. If no notification exists, a new
        ``ProductNotification`` will be created for the product. A newly
        created ``ProductNotification`` will be set to status ``ACTIVE``
        immediately.
        """
        notification, created = ProductNotification.objects.get_or_create(
            user=self.request.user,
            product=self.product,
        )

        if created:
            notification.status = ProductNotification.ACTIVE
            notification.save()
        return notification, created

    def send_confirmation_email(self, notification):
        """
        Send email message to unregistered user's email address containing
        a confirmation URL and a unsubscribe URL. This is the only means
        for the user to active and deactivate their notification.
        """
        template = loader.get_template(self.email_template)
        context = Context({
            'site': Site.objects.get_current(),
            'notification': notification,
            'product': self.product,
        })

        msg = mail.EmailMessage(
            _("[Confirmation] Please confirm the notification for "
              "product %s") % (self.product.title,),
            template.render(context),
            settings.OSCAR_FROM_EMAIL,
            [notification.email],
        )
        msg.send()
        messages.info(self.request,
                      _("Confirmation email send successfully, "
                        "please check your email."))

    def form_valid(self, form):
        """
        Handle creating a new ``ProductNotification`` when no errors
        have been found in form. If a user has already signed up for
        this ``ProductNotification``, no new notification will be
        created but the user will receive confirmation that the notification
        was created successfully. This reduces the complexity of handling
        this situation differently from a new notification and the user
        does not get annoyed by realising that they have already signed
        up and just forgot about it.
        If a new notification is created for an unregistered user, an
        email is sent out with a confirmation and unsubscibe URL. A
        registered users notification is activated immediately.

        NOTE: a registered user that is not logged in will be redirected
        to the login page. This is achieved by checking if an anonymous
        email address is already part of a registered customer account.
        """
        is_authenticated = self.request.user.is_authenticated()
        self.product = self.get_product()

        # first check if the anonymous user provided an email address
        # that belongs to a registered user. If that is the case the
        # user will be redirected to the login/register page
        if not is_authenticated:
            try:
                User.objects.get(email=form.cleaned_data['email'])
                redirect_url = "%s?next=%s" % (reverse('customer:login'),
                                               self.get_success_url())
                return HttpResponseRedirect(redirect_url)
            except User.DoesNotExist:
                pass

        if is_authenticated:
            notification, created = self.get_notification_for_authenticated_user()
        else:
            notification, created = self.get_notification_for_anonymous_user(
                form.cleaned_data['email']
            )

        if not created:
            messages.success(self.request,
                     _("you have signed up for a "
                       "notification of '%s' already") % self.product.title)
            return HttpResponseRedirect(self.get_success_url())

        if created and not is_authenticated:
            self.send_confirmation_email(notification)

        messages.success(self.request,
                _("%s was added to your notifications") % self.product.title)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        """
        Get success URL to redirect to the product's detail page.
        """
        return reverse('catalogue:detail', kwargs={
            'product_slug':self.product.slug,
            'pk': self.product.pk
        })


class ProductNotificationSetStatusView(generic.TemplateView):
    """
    View to change the status of a product notification. The status can
    be changed from ``active`` to ``inactive`` and vice versa.
    """
    model = ProductNotification
    status_types = [map[0] for map in ProductNotification.STATUS_TYPES]
    pk_url_kwarg = 'notification_pk'

    def get(self, *args, **kwargs):
        """
        Handle GET request for this view. Extract the product and notification
        from the URL as well as the new status. If the status is not ``active``
        or ``inactive`` a HTTP redirect is returned without changing the
        notification. Otherwise the notification status is updated
        """
        self.product = get_object_or_404(Product, pk=kwargs.get('pk'))
        status = kwargs.get('status', None)

        if status in (self.status_types):
            notification = get_object_or_404(self.model, pk=kwargs.get('pk'))
            notification.status = status
            notification.save()

        return HttpResponseRedirect(self.get_success_url())

    def post(self, *args, **kwargs):
        """
        Handle POST request for this view similar to the GET request. Ignores
        any POST request parameters. Extract the product and notification
        from the URL as well as the new status. If the status is not ``active``
        or ``inactive`` a HTTP redirect is returned without changing the
        notification. Otherwise the notification status is updated
        """
        return self.get(*args, **kwargs)

    def get_success_url(self):
        """
        Get URL to redirect to after successful status change.
        """
        detail_url = reverse('catalogue:detail',
                             args=(self.product.slug, self.product.pk))
        return self.request.META.get('HTTP_REFERER', detail_url)
