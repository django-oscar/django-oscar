import random
from django.conf import settings
from django.http import Http404
from django.views import generic

from django.db.models import get_model
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from oscar.apps.catalogue.notification.models import NotificationList
from oscar.apps.catalogue.notification.forms import NotificationForm

Product = get_model('catalogue', 'product')


class UnsubscribeNotificationView(generic.TemplateView):
    """
    This view is meant to disable product Notifications
    """
    template_name = 'notification/unsubscribe.html'

    def get_notification(self, key, email):
        if key is None or email is None:
            raise Http404
        try:
            return NotificationList.objects.get(unsubscribe_key=key, email=email)
        except NotificationList.DoesNotExist:
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
            return NotificationList.objects.get(confirm_key=key, email=email)
        except NotificationList.DoesNotExist:
            raise Http404

    def get(self, *args, **kwargs):
        self.object = self.get_notification(kwargs.get('key', None),
                                            self.request.GET.get('email', None))
        self.object.active = True
        self.object.save()
        return super(ConfirmNotificationView, self).get(*args, **kwargs)

from django.forms.formsets import formset_factory

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

    def form_valid(self, form):
        self.product = self.get_product()

        is_authenticated = self.request.user.is_authenticated()
        if is_authenticated:
            # search for previous product subscriptions from this user
            self.notification, created = NotificationList.objects.get_or_create(
                user=self.request.user,
                email=self.request.user.email
            )
            mobile_number = form.cleaned_data.get('mobile_number', None)
            if mobile_number:
                self.request.user.userprofile.mobile_no = mobile_number
                self.request.user.userprofile.save()
        else:
            self.notification, created = NotificationList.objects.get_or_create(
                                                email=form.cleaned_data['email']
                                        )
        if created:
            # if notification was created, generate a key for mark a False
            # active for unkwn user
            alphabet = [chr(x) for x in range(ord('A'), ord('Z') + 1)]
            keys = [''.join([random.choice(alphabet) for i in range(0, 16)]),
                    ''.join([random.choice(alphabet) for i in range(0, 16)]),
                    ''.join([random.choice(alphabet) for i in range(0, 32)])]
            self.notification.confirm_key =  keys[0]
            self.notification.unsubscribe_key = keys[1]
            self.notification.persistence_key = keys[2]
            self.notification.active = True if is_authenticated else False
            self.notification.save()
            # TODO : send an email confirmation email in case is annonymous
            if not is_authenticated:
                messages.info(self.request,
                        "Check your email to confirm this subscription")

        # now add the required product to the notification list
        self.notification.productnotification_set.get_or_create(
            product=self.product
        )
        messages.success(self.request,
                "%s was added to your notification list" % self.product.title)
        return super(self.__class__, self).form_valid(form)

    def get_success_url(self):
        return reverse('catalogue:detail', kwargs={
                                        'product_slug': self.product.slug,
                                        "pk": self.product.pk})


class DeleteProductNotificationView(generic.FormView):
    pass
