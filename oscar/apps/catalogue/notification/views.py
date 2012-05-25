import sha
import random
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.views import generic

from django.db.models import get_model
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from oscar.apps.catalogue.notification.forms import NotificationForm

Product = get_model('catalogue', 'product')
ProductNotification = get_model('notification', 'productnotification')


class UnsubscribeNotificationView(generic.TemplateView):
    """
    This view is meant to disable product Notifications
    """
    template_name = 'notification/unsubscribe.html'

    def get_notification(self, key, email):
        if key is None or email is None:
            raise Http404
        try:
            return ProductNotification.objects.get(unsubscribe_key=key, email=email)
        except ProductNotification.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        self.object = self.get_notification(kwargs.get('key', None),
                                            self.request.GET.get('email', None))
        self.object.active = False
        self.object.save()
        return super(UnsubscribeNotificationView, self).get(*args, **kwargs)


class ConfirmNotificationView(generic.TemplateView):
    """
    This view will care about notification activations
    """
    template_name = 'notification/confirm.html'

    def get_context_data(self, **kwargs):
        params = {}
        params['notification'] = self.object
        return params

    def get_notification(self, key, email):
        if key is None or email is None:
            raise Http404
        try:
            return ProductNotification.objects.get(confirm_key=key, email=email)
        except ProductNotification.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        self.object = self.get_notification(kwargs.get('key', None),
                                            self.request.GET.get('email', None))
        self.object.active = True
        self.object.save()
        return super(ConfirmNotificationView, self).get(*args, **kwargs)


class CreateProductNotificationView(generic.FormView):
    """
    Add a new product to the users notification list.
    """
    template_name = 'notification/notification.html'
    product_model = Product
    form_class = NotificationForm

    def get_form_kwargs(self):
        kwargs = super(self.__class__, self).get_form_kwargs()

        user = self.request.user
        if user.is_authenticated():
            kwargs['initial'].update({'email': user.email})
        return kwargs

    def get_product(self):
        return get_object_or_404(self.product_model, pk=self.kwargs['product_pk'])

    def get_context_data(self, *args, **kwargs):
        ctx = super(self.__class__, self).get_context_data(*args, **kwargs)
        ctx['product'] = self.get_product()
        return ctx

    def generate_random_key(self, email):
        salt = sha.new(str(random.random())).hexdigest()
        return sha.new(salt+str(email)).hexdigest()

    def get_notification_for_anonymous_user(self, email):
        notification, created = ProductNotification.objects.get_or_create(
            email=email,
            product=self.product,
        )

        if created: 
            notification.status = ProductNotification.UNCONFIRMED
            notification.confirm_key = self.generate_random_key(anonymous_email)
            notification.unsubscribe_key = self.generate_random_key(anonymous_email)
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

    def form_valid(self, form):
        is_authenticated = self.request.user.is_authenticated()
        self.product = self.get_product()

        # first check if the anonymous user provided an email address
        # that belongs to a registered user. If that is the case the
        # user will be redirected to the login/register page
        if not is_authenticated:
            try:
                user = User.objects.get(email=form.cleaned_data['email'])
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
            # create keys for anonymous users leave blank for users that
            # are registered as they can manage their subscriptions in
            # their account settings

            # TODO : send an email confirmation email in case is annonymous
            messages.info(self.request,
                    "Check your email to confirm this subscription")

        messages.success(self.request,
                "%s was added to your notifications" % self.product.title)

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse('catalogue:detail',
                       args=(self.product.slug, self.product.pk))


class DeleteProductNotificationView(generic.FormView):
    pass
