from django.conf import settings
from django.views import generic
from django.http import HttpResponseRedirect

from django.core import mail
from django.contrib import messages
from django.db.models import get_model
from django.template import loader, Context
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from oscar.apps.catalogue.notification.forms import NotificationForm

Product = get_model('catalogue', 'product')
ProductNotification = get_model('notification', 'productnotification')


class NotificationDetailView(generic.DetailView):
    """
    Detailed view of a product notification.
    """
    model = ProductNotification
    context_object_name = 'notification'

    def get_object(self, queryset=None):
        key = self.kwargs.get('key', 'invalid')
        return get_object_or_404(ProductNotification, confirm_key=key)


class NotificationUnsubscribeView(NotificationDetailView):
    """
    View to inactivate notifications for anonymous users.
    """
    template_name = 'notification/unsubscribe.html'

    def get(self, *args, **kwargs):
        notification = self.get_object()
        notification.status = ProductNotification.INACTIVE
        notification.save()
        messages.info(self.request,
            _("You have successfully unsubscribed from this notification.")
        )
        return super(NotificationUnsubscribeView, self).get(*args, **kwargs)


class NotificationConfirmView(NotificationDetailView):
    """
    View to confirm the email address of an anonymous user used to
    sign up for a product notification.
    """
    template_name = 'notification/confirm.html'

    def get(self, *args, **kwargs):
        notification = self.get_object()
        notification.status = ProductNotification.ACTIVE
        notification.save()
        messages.info(self.request,
            _("Yeah! You have confirmed your subscription. We'll notify "
              "you as soon as the product is back in stock.")
        )
        return super(NotificationConfirmView, self).get(*args, **kwargs)


class ProductNotificationCreateView(generic.FormView):
    """
    View to create a new product notification based on a registered user
    or an email address provided by an anonymous user.
    """
    product_model = Product
    form_class = NotificationForm
    template_name = 'notification/notification.html'
    email_template = 'notification/email.html'

    def get_form_kwargs(self):
        kwargs = super(ProductNotificationCreateView, self).get_form_kwargs()

        user = self.request.user
        if user.is_authenticated():
            kwargs['initial'].update({'email': user.email})
        return kwargs

    def get_product(self):
        return get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])

    def get_context_data(self, *args, **kwargs):
        ctx = super(ProductNotificationCreateView, self).get_context_data(*args, **kwargs)
        ctx['product'] = self.get_product()
        return ctx

    def get_notification_for_anonymous_user(self, email):
        notification, created = ProductNotification.objects.get_or_create(
            email=email,
            product=self.product,
        )

        if created:
            notification.status = ProductNotification.UNCONFIRMED
            notification.save()
        return notification, created

    def get_notification_for_authenticated_user(self):
        notification, created = ProductNotification.objects.get_or_create(
            user=self.request.user,
            product=self.product,
        )

        if created:
            notification.status = ProductNotification.ACTIVE
            notification.save()
        return notification, created

    def send_confirmation_email(self, notification):
        template = loader.get_template(self.email_template)
        context = Context({
            'site': Site.objects.get(pk=getattr(settings, 'SITE_ID', 1)),
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
                "%s was added to your notifications" % self.product.title)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('catalogue:detail',
                       args=(self.product.slug, self.product.pk))


class ProductNotificationSetStatusView(generic.TemplateView):
    """
    View to change the status of a product notification. The status can
    be changed from ``active`` to ``inactive`` and vice versa.
    """
    model = ProductNotification
    status_types = [map[0] for map in ProductNotification.STATUS_TYPES]

    def get(self, *args, **kwargs):
        """
        Handle GET request for this view. Extract the product and notification
        from the URL as well as the new status. If the status is not ``active``
        or ``inactive`` a HTTP redirect is returned without changing the
        notification. Otherwise the notification status is updated
        """
        self.product= get_object_or_404(Product, pk=kwargs.get('product_pk'))
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

class ProductNotificationDeleteView(generic.DeleteView):
    """
    View to delete a product notification. This should not be available
    to the users as their can only activate and deactivate notifications.
    It should be checked for logged in staff member.
    """
    model = ProductNotification
    template_name = 'notification/delete.html'

    def get_success_url(self):
        #return reverse('dashboard:notification-list')
        return reverse('dashboard:index')
