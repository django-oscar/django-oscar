import json

import phonenumbers
from django import forms
from django.contrib import messages
from django.core import validators
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import six
from django.utils.encoding import smart_str
from django.utils.six.moves import map
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from phonenumber_field.phonenumber import PhoneNumber

from oscar.core.utils import safe_referrer


class PostActionMixin(object):
    """
    Simple mixin to forward POST request that contain a key 'action'
    onto a method of form "do_{action}".

    This only works with DetailView
    """
    def post(self, request, *args, **kwargs):
        if 'action' in self.request.POST:
            model = self.get_object()
            # The do_* method is required to do what it needs to with the model
            # it is passed, and then to assign the HTTP response to
            # self.response.
            method_name = "do_%s" % self.request.POST['action'].lower()
            if hasattr(self, method_name):
                getattr(self, method_name)(model)
                return self.response
            else:
                messages.error(request, _("Invalid form submission"))
        return super(PostActionMixin, self).post(request, *args, **kwargs)


class BulkEditMixin(object):
    """
    Mixin for views that have a bulk editing facility.  This is normally in the
    form of tabular data where each row has a checkbox.  The UI allows a number
    of rows to be selected and then some 'action' to be performed on them.
    """
    action_param = 'action'

    # Permitted methods that can be used to act on the selected objects
    actions = None
    checkbox_object_name = None

    def get_checkbox_object_name(self):
        if self.checkbox_object_name:
            return self.checkbox_object_name
        return smart_str(self.model._meta.object_name.lower())

    def get_error_url(self, request):
        return safe_referrer(request, '.')

    def get_success_url(self, request):
        return safe_referrer(request, '.')

    def post(self, request, *args, **kwargs):
        # Dynamic dispatch pattern - we forward POST requests onto a method
        # designated by the 'action' parameter.  The action has to be in a
        # whitelist to avoid security issues.
        action = request.POST.get(self.action_param, '').lower()
        if not self.actions or action not in self.actions:
            messages.error(self.request, _("Invalid action"))
            return redirect(self.get_error_url(request))

        ids = request.POST.getlist(
            'selected_%s' % self.get_checkbox_object_name())
        ids = list(map(int, ids))
        if not ids:
            messages.error(
                self.request,
                _("You need to select some %ss")
                % self.get_checkbox_object_name())
            return redirect(self.get_error_url(request))

        objects = self.get_objects(ids)
        return getattr(self, action)(request, objects)

    def get_objects(self, ids):
        object_dict = self.get_object_dict(ids)
        # Rearrange back into the original order
        return [object_dict[id] for id in ids]

    def get_object_dict(self, ids):
        return self.get_queryset().in_bulk(ids)


class ObjectLookupView(View):
    """Base view for json lookup for objects"""
    def get_queryset(self):
        return self.model.objects.all()

    def format_object(self, obj):
        return {
            'id': obj.pk,
            'text': six.text_type(obj),
        }

    def initial_filter(self, qs, value):
        return qs.filter(pk__in=value.split(','))

    def lookup_filter(self, qs, term):
        return qs

    def paginate(self, qs, page, page_limit):
        total = qs.count()

        start = (page - 1) * page_limit
        stop = start + page_limit

        qs = qs[start:stop]

        return qs, (page_limit * page < total)

    def get_args(self):
        GET = self.request.GET
        return (GET.get('initial', None),
                GET.get('q', None),
                int(GET.get('page', 1)),
                int(GET.get('page_limit', 20)))

    def get(self, request):
        self.request = request
        qs = self.get_queryset()

        initial, q, page, page_limit = self.get_args()

        if initial:
            qs = self.initial_filter(qs, initial)
            more = False
        else:
            if q:
                qs = self.lookup_filter(qs, q)
            qs, more = self.paginate(qs, page, page_limit)

        return HttpResponse(json.dumps({
            'results': [self.format_object(obj) for obj in qs],
            'more': more,
        }), content_type='application/json')


class PhoneNumberMixin(object):
    """Validation mixin for forms with a phone number, and optionally a country.

    It tries to validate the phone number, and on failure tries to validate it
    using a hint (the country provided), and treating it as a local number.

    """

    def __init__(self, *args, **kwargs):
        super(PhoneNumberMixin, self).__init__(*args, **kwargs)

        # We can't use the PhoneNumberField here since we want validate the
        # phonenumber based on the selected country as a fallback when a local
        # number is entered. We add the field in the init since on Python 2
        # using forms.Form as base class results in errors when using this
        # class as mixin.
        field_kwargs = {
            'required': False,
            'help_text': '',
            'max_length': 32,
            'label': _('Phone number'),
        }

        # If the model field already exists, copy existing properties from it
        for key in field_kwargs:
            try:
                field_kwargs[key] = getattr(self.fields['phone_number'], key)
            except (KeyError, AttributeError):
                pass

        self.fields['phone_number'] = forms.CharField(**field_kwargs)

    def get_country(self):
        # If the form data contains valid country information, we use that.
        if hasattr(self, 'cleaned_data') and 'country' in self.cleaned_data:
            return self.cleaned_data['country']
        # Oscar hides the field if there's only one country. Then (and only
        # then!) can we consider a country on the model instance.
        elif 'country' not in self.fields and hasattr(self.instance, 'country'):
            return self.instance.country

    def get_region_code(self, country):
        return country.iso_3166_1_a2

    def clean_phone_number(self):
        number = self.cleaned_data['phone_number']

        # empty
        if number in validators.EMPTY_VALUES:
            return ''

        # Check for an international phone format
        try:
            phone_number = PhoneNumber.from_string(number)
        except phonenumbers.NumberParseException:
            # Try hinting with the shipping country if we can determine one
            country = self.get_country()
            region_code = self.get_region_code(country) if country else None

            if not region_code:
                # There is no shipping country, not a valid international
                # number
                raise ValidationError(
                    _(u'This is not a valid international phone format.'))

            # The PhoneNumber class does not allow specifying
            # the region. So we drop down to the underlying phonenumbers
            # library, which luckily allows parsing into a PhoneNumber
            # instance
            try:
                phone_number = PhoneNumber.from_string(number, region=region_code)
                if not phone_number.is_valid():
                    raise ValidationError(
                        _(u'This is not a valid local phone format for %s.')
                        % country)
            except phonenumbers.NumberParseException:
                # Not a valid local or international phone number
                raise ValidationError(
                    _(u'This is not a valid local or international phone'
                      u' format.'))

        return phone_number
