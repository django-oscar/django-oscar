import datetime
from collections import OrderedDict
from decimal import Decimal as D
from decimal import InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Count, Q, Sum, fields
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, UpdateView

from oscar.apps.order import exceptions as order_exceptions
from oscar.apps.payment.exceptions import PaymentError
from oscar.core.compat import UnicodeCSVWriter
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

Partner = get_model('partner', 'Partner')
Transaction = get_model('payment', 'Transaction')
SourceType = get_model('payment', 'SourceType')
Order = get_model('order', 'Order')
OrderNote = get_model('order', 'OrderNote')
ShippingAddress = get_model('order', 'ShippingAddress')
Line = get_model('order', 'Line')
ShippingEventType = get_model('order', 'ShippingEventType')
PaymentEventType = get_model('order', 'PaymentEventType')
EventHandler = get_class('order.processing', 'EventHandler')
OrderStatsForm = get_class('dashboard.orders.forms', 'OrderStatsForm')
OrderSearchForm = get_class('dashboard.orders.forms', 'OrderSearchForm')
OrderNoteForm = get_class('dashboard.orders.forms', 'OrderNoteForm')
ShippingAddressForm = get_class(
    'dashboard.orders.forms', 'ShippingAddressForm')
OrderStatusForm = get_class('dashboard.orders.forms', 'OrderStatusForm')


def queryset_orders_for_user(user):
    """
    Returns a queryset of all orders that a user is allowed to access.
    A staff user may access all orders.
    To allow access to an order for a non-staff user, at least one line's
    partner has to have the user in the partner's list.
    """
    queryset = Order._default_manager.select_related(
        'billing_address', 'billing_address__country',
        'shipping_address', 'shipping_address__country',
        'user'
    ).prefetch_related('lines')
    if user.is_staff:
        return queryset
    else:
        partners = Partner._default_manager.filter(users=user)
        return queryset.filter(lines__partner__in=partners).distinct()


def get_order_for_user_or_404(user, number):
    try:
        return queryset_orders_for_user(user).get(number=number)
    except ObjectDoesNotExist:
        raise Http404()


class OrderStatsView(FormView):
    """
    Dashboard view for order statistics.
    Supports the permission-based dashboard.
    """
    template_name = 'dashboard/orders/statistics.html'
    form_class = OrderStatsForm

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        ctx = self.get_context_data(form=form,
                                    filters=form.get_filters())
        return self.render_to_response(ctx)

    def get_form_kwargs(self):
        kwargs = super(OrderStatsView, self).get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(OrderStatsView, self).get_context_data(**kwargs)
        filters = kwargs.get('filters', {})
        ctx.update(self.get_stats(filters))
        ctx['title'] = kwargs['form'].get_filter_description()
        return ctx

    def get_stats(self, filters):
        orders = queryset_orders_for_user(self.request.user).filter(**filters)
        stats = {
            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),
            'total_revenue': orders.aggregate(
                Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'order_status_breakdown': orders.order_by('status').values(
                'status').annotate(freq=Count('id'))
        }
        return stats


class OrderListView(BulkEditMixin, ListView):
    """
    Dashboard view for a list of orders.
    Supports the permission-based dashboard.
    """
    model = Order
    context_object_name = 'orders'
    template_name = 'dashboard/orders/order_list.html'
    form_class = OrderSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    actions = ('download_selected_orders', 'change_order_statuses')

    def dispatch(self, request, *args, **kwargs):
        # base_queryset is equal to all orders the user is allowed to access
        self.base_queryset = queryset_orders_for_user(
            request.user).order_by('-date_placed')
        return super(OrderListView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if 'order_number' in request.GET and request.GET.get(
                'response_format', 'html') == 'html':
            # Redirect to Order detail page if valid order number is given
            try:
                order = self.base_queryset.get(
                    number=request.GET['order_number'])
            except Order.DoesNotExist:
                pass
            else:
                return redirect(
                    'dashboard:order-detail', number=order.number)
        return super(OrderListView, self).get(request, *args, **kwargs)

    def get_queryset(self):  # noqa (too complex (19))
        """
        Build the queryset for this list.
        """
        queryset = sort_queryset(self.base_queryset, self.request,
                                 ['number', 'total_incl_tax'])

        # Look for shortcut query filters
        if 'order_status' in self.request.GET:
            self.form = self.form_class()
            status = self.request.GET['order_status']
            if status.lower() == 'none':
                status = None
            return self.base_queryset.filter(status=status)

        if 'order_number' not in self.request.GET:
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['order_number']:
            queryset = self.base_queryset.filter(
                number__istartswith=data['order_number'])

        if data['name']:
            # If the value is two words, then assume they are first name and
            # last name
            parts = data['name'].split()
            allow_anon = getattr(settings, 'OSCAR_ALLOW_ANON_CHECKOUT', False)

            if len(parts) == 1:
                parts = [data['name'], data['name']]
            else:
                parts = [parts[0], parts[1:]]

            filter = Q(user__first_name__istartswith=parts[0])
            filter |= Q(user__last_name__istartswith=parts[1])
            if allow_anon:
                filter |= Q(billing_address__first_name__istartswith=parts[0])
                filter |= Q(shipping_address__first_name__istartswith=parts[0])
                filter |= Q(billing_address__last_name__istartswith=parts[1])
                filter |= Q(shipping_address__last_name__istartswith=parts[1])

            queryset = queryset.filter(filter).distinct()

        if data['product_title']:
            queryset = queryset.filter(
                lines__title__istartswith=data['product_title']).distinct()

        if data['upc']:
            queryset = queryset.filter(lines__upc=data['upc'])

        if data['partner_sku']:
            queryset = queryset.filter(lines__partner_sku=data['partner_sku'])

        if data['date_from'] and data['date_to']:
            date_to = datetime_combine(data['date_to'], datetime.time.max)
            date_from = datetime_combine(data['date_from'], datetime.time.min)
            queryset = queryset.filter(
                date_placed__gte=date_from, date_placed__lt=date_to)
        elif data['date_from']:
            date_from = datetime_combine(data['date_from'], datetime.time.min)
            queryset = queryset.filter(date_placed__gte=date_from)
        elif data['date_to']:
            date_to = datetime_combine(data['date_to'], datetime.time.max)
            queryset = queryset.filter(date_placed__lt=date_to)

        if data['voucher']:
            queryset = queryset.filter(
                discounts__voucher_code=data['voucher']).distinct()

        if data['payment_method']:
            queryset = queryset.filter(
                sources__source_type__code=data['payment_method']).distinct()

        if data['status']:
            queryset = queryset.filter(status=data['status'])

        return queryset

    def get_search_filter_descriptions(self):  # noqa (too complex (19))
        """Describe the filters used in the search.

        These are user-facing messages describing what filters
        were used to filter orders in the search query.

        Returns:
            list of unicode messages

        """
        descriptions = []

        # Attempt to retrieve data from the submitted form
        # If the form hasn't been submitted, then `cleaned_data`
        # won't be set, so default to None.
        data = getattr(self.form, 'cleaned_data', None)

        if data is None:
            return descriptions

        if data.get('order_number'):
            descriptions.append(
                _('Order number starts with "{order_number}"').format(
                    order_number=data['order_number']
                )
            )

        if data.get('name'):
            descriptions.append(
                _('Customer name matches "{customer_name}"').format(
                    customer_name=data['name']
                )
            )

        if data.get('product_title'):
            descriptions.append(
                _('Product name matches "{product_name}"').format(
                    product_name=data['product_title']
                )
            )

        if data.get('upc'):
            descriptions.append(
                # Translators: "UPC" means "universal product code" and it is
                # used to uniquely identify a product in an online store.
                # "Item" in this context means an item in an order placed
                # in an online store.
                _('Includes an item with UPC "{upc}"').format(
                    upc=data['upc']
                )
            )

        if data.get('partner_sku'):
            descriptions.append(
                # Translators: "SKU" means "stock keeping unit" and is used to
                # identify products that can be shipped from an online store.
                # A "partner" is a company that ships items to users who
                # buy things in an online store.
                _('Includes an item with partner SKU "{partner_sku}"').format(
                    partner_sku=data['partner_sku']
                )
            )

        if data.get('date_from') and data.get('date_to'):
            descriptions.append(
                # Translators: This string refers to orders in an online
                # store that were made within a particular date range.
                _('Placed between {start_date} and {end_date}').format(
                    start_date=data['date_from'],
                    end_date=data['date_to']
                )
            )

        elif data.get('date_from'):
            descriptions.append(
                # Translators: This string refers to orders in an online store
                # that were made after a particular date.
                _('Placed after {start_date}').format(
                    start_date=data['date_from'])
            )

        elif data.get('date_to'):
            end_date = data['date_to'] + datetime.timedelta(days=1)
            descriptions.append(
                # Translators: This string refers to orders in an online store
                # that were made before a particular date.
                _('Placed before {end_date}').format(end_date=end_date)
            )

        if data.get('voucher'):
            descriptions.append(
                # Translators: A "voucher" is a coupon that can be applied to
                # an order in an online store in order to receive a discount.
                # The voucher "code" is a string that users can enter to
                # receive the discount.
                _('Used voucher code "{voucher_code}"').format(
                    voucher_code=data['voucher'])
            )

        if data.get('payment_method'):
            payment_type = SourceType.objects.get(code=data['payment_method'])
            descriptions.append(
                # Translators: A payment method is a way of paying for an
                # item in an online store.  For example, a user can pay
                # with a credit card or PayPal.
                _('Paid using {payment_method}').format(
                    payment_method=payment_type.name
                )
            )

        if data.get('status'):
            descriptions.append(
                # Translators: This string refers to an order in an
                # online store.  Some examples of order status are
                # "purchased", "cancelled", or "refunded".
                _('Order status is {order_status}').format(
                    order_status=data['status'])
            )

        return descriptions

    def get_context_data(self, **kwargs):
        ctx = super(OrderListView, self).get_context_data(**kwargs)
        ctx['form'] = self.form
        ctx['order_statuses'] = Order.all_statuses()
        ctx['search_filters'] = self.get_search_filter_descriptions()
        return ctx

    def is_csv_download(self):
        return self.request.GET.get('response_format', None) == 'csv'

    def get_paginate_by(self, queryset):
        return None if self.is_csv_download() else self.paginate_by

    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_download():
            return self.download_selected_orders(
                self.request,
                context['object_list'])
        return super(OrderListView, self).render_to_response(
            context, **response_kwargs)

    def get_download_filename(self, request):
        return 'orders.csv'

    def download_selected_orders(self, request, orders):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' \
            % self.get_download_filename(request)
        writer = UnicodeCSVWriter(open_file=response)

        meta_data = (('number', _('Order number')),
                     ('value', _('Order value')),
                     ('date', _('Date of purchase')),
                     ('num_items', _('Number of items')),
                     ('status', _('Order status')),
                     ('customer', _('Customer email address')),
                     ('shipping_address_name', _('Deliver to name')),
                     ('billing_address_name', _('Bill to name')),
                     )
        columns = OrderedDict()
        for k, v in meta_data:
            columns[k] = v

        writer.writerow(columns.values())
        for order in orders:
            row = columns.copy()
            row['number'] = order.number
            row['value'] = order.total_incl_tax
            row['date'] = format_datetime(order.date_placed, 'DATETIME_FORMAT')
            row['num_items'] = order.num_items
            row['status'] = order.status
            row['customer'] = order.email
            if order.shipping_address:
                row['shipping_address_name'] = order.shipping_address.name
            else:
                row['shipping_address_name'] = ''
            if order.billing_address:
                row['billing_address_name'] = order.billing_address.name
            else:
                row['billing_address_name'] = ''
            writer.writerow(row.values())
        return response

    def change_order_statuses(self, request, orders):
        for order in orders:
            self.change_order_status(request, order)
        return redirect('dashboard:order-list')

    def change_order_status(self, request, order):
        # This method is pretty similar to what
        # OrderDetailView.change_order_status does. Ripe for refactoring.
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid")
                           % new_status)
        elif new_status not in order.available_statuses():
            messages.error(request, _("The new status '%s' is not valid for"
                                      " this order") % new_status)
        else:
            handler = EventHandler(request.user)
            old_status = order.status
            try:
                handler.handle_order_status_change(order, new_status)
            except PaymentError as e:
                messages.error(request, _("Unable to change order status due"
                                          " to payment error: %s") % e)
            else:
                msg = _("Order status changed from '%(old_status)s' to"
                        " '%(new_status)s'") % {'old_status': old_status,
                                                'new_status': new_status}
                messages.info(request, msg)
                order.notes.create(
                    user=request.user, message=msg, note_type=OrderNote.SYSTEM)


class OrderDetailView(DetailView):
    """
    Dashboard view to display a single order.

    Supports the permission-based dashboard.
    """
    model = Order
    context_object_name = 'order'
    template_name = 'dashboard/orders/order_detail.html'

    # These strings are method names that are allowed to be called from a
    # submitted form.
    order_actions = ('save_note', 'delete_note', 'change_order_status',
                     'create_order_payment_event')
    line_actions = ('change_line_statuses', 'create_shipping_event',
                    'create_payment_event')

    def get_object(self, queryset=None):
        return get_order_for_user_or_404(
            self.request.user, self.kwargs['number'])

    def post(self, request, *args, **kwargs):
        # For POST requests, we use a dynamic dispatch technique where a
        # parameter specifies what we're trying to do with the form submission.
        # We distinguish between order-level actions and line-level actions.

        order = self.object = self.get_object()

        # Look for order-level action first
        if 'order_action' in request.POST:
            return self.handle_order_action(
                request, order, request.POST['order_action'])

        # Look for line-level action
        if 'line_action' in request.POST:
            return self.handle_line_action(
                request, order, request.POST['line_action'])

        return self.reload_page(error=_("No valid action submitted"))

    def handle_order_action(self, request, order, action):
        if action not in self.order_actions:
            return self.reload_page(error=_("Invalid action"))
        return getattr(self, action)(request, order)

    def handle_line_action(self, request, order, action):
        if action not in self.line_actions:
            return self.reload_page(error=_("Invalid action"))

        # Load requested lines
        line_ids = request.POST.getlist('selected_line')
        if len(line_ids) == 0:
            return self.reload_page(error=_(
                "You must select some lines to act on"))
        lines = order.lines.filter(id__in=line_ids)
        if len(line_ids) != len(lines):
            return self.reload_page(error=_("Invalid lines requested"))

        # Build list of line quantities
        line_quantities = []
        for line in lines:
            qty = request.POST.get('selected_line_qty_%s' % line.id)
            try:
                qty = int(qty)
            except ValueError:
                qty = None
            if qty is None or qty <= 0:
                error_msg = _("The entered quantity for line #%s is not valid")
                return self.reload_page(error=error_msg % line.id)
            elif qty > line.quantity:
                error_msg = _(
                    "The entered quantity for line #%(line_id)s "
                    "should not be higher than %(quantity)s")
                kwargs = {'line_id': line.id, 'quantity': line.quantity}
                return self.reload_page(error=error_msg % kwargs)

            line_quantities.append(qty)

        return getattr(self, action)(
            request, order, lines, line_quantities)

    def reload_page(self, fragment=None, error=None):
        url = reverse('dashboard:order-detail',
                      kwargs={'number': self.object.number})
        if fragment:
            url += '#' + fragment
        if error:
            messages.error(self.request, error)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        ctx = super(OrderDetailView, self).get_context_data(**kwargs)
        ctx['active_tab'] = kwargs.get('active_tab', 'lines')

        # Forms
        ctx['note_form'] = self.get_order_note_form()
        ctx['order_status_form'] = self.get_order_status_form()

        ctx['line_statuses'] = Line.all_statuses()
        ctx['shipping_event_types'] = ShippingEventType.objects.all()
        ctx['payment_event_types'] = PaymentEventType.objects.all()

        ctx['payment_transactions'] = self.get_payment_transactions()

        return ctx

    # Data fetching methods for template context

    def get_payment_transactions(self):
        return Transaction.objects.filter(
            source__order=self.object)

    def get_order_note_form(self):
        kwargs = {
            'order': self.object,
            'user': self.request.user,
            'data': None
        }
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        note_id = self.kwargs.get('note_id', None)
        if note_id:
            note = get_object_or_404(OrderNote, order=self.object, id=note_id)
            if note.is_editable():
                kwargs['instance'] = note
        return OrderNoteForm(**kwargs)

    def get_order_status_form(self):
        data = None
        if self.request.method == 'POST':
            data = self.request.POST
        return OrderStatusForm(order=self.object, data=data)

    # Order-level actions

    def save_note(self, request, order):
        form = self.get_order_note_form()
        if form.is_valid():
            form.save()
            messages.success(self.request, _("Note saved"))
            return self.reload_page(fragment='notes')

        ctx = self.get_context_data(note_form=form, active_tab='notes')
        return self.render_to_response(ctx)

    def delete_note(self, request, order):
        try:
            note = order.notes.get(id=request.POST.get('note_id', None))
        except ObjectDoesNotExist:
            messages.error(request, _("Note cannot be deleted"))
        else:
            messages.info(request, _("Note deleted"))
            note.delete()
        return self.reload_page()

    def change_order_status(self, request, order):
        form = self.get_order_status_form()
        if not form.is_valid():
            return self.reload_page(error=_("Invalid form submission"))

        old_status, new_status = order.status, form.cleaned_data['new_status']
        handler = EventHandler(request.user)

        success_msg = _(
            "Order status changed from '%(old_status)s' to "
            "'%(new_status)s'") % {'old_status': old_status,
                                   'new_status': new_status}
        try:
            handler.handle_order_status_change(
                order, new_status, note_msg=success_msg)
        except PaymentError as e:
            messages.error(
                request, _("Unable to change order status due to "
                           "payment error: %s") % e)
        except order_exceptions.InvalidOrderStatus as e:
            # The form should validate against this, so we should only end up
            # here during race conditions.
            messages.error(
                request, _("Unable to change order status as the requested "
                           "new status is not valid"))
        else:
            messages.info(request, success_msg)
        return self.reload_page()

    def create_order_payment_event(self, request, order):
        """
        Create a payment event for the whole order
        """
        amount_str = request.POST.get('amount', None)
        try:
            amount = D(amount_str)
        except InvalidOperation:
            messages.error(request, _("Please choose a valid amount"))
            return self.reload_page()
        return self._create_payment_event(request, order, amount)

    # Line-level actions

    def change_line_statuses(self, request, order, lines, quantities):
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid")
                           % new_status)
            return self.reload_page()
        errors = []
        for line in lines:
            if new_status not in line.available_statuses():
                errors.append(_("'%(status)s' is not a valid new status for"
                                " line %(line_id)d") % {'status': new_status,
                                                        'line_id': line.id})
        if errors:
            messages.error(request, "\n".join(errors))
            return self.reload_page()

        msgs = []
        for line in lines:
            msg = _("Status of line #%(line_id)d changed from '%(old_status)s'"
                    " to '%(new_status)s'") % {'line_id': line.id,
                                               'old_status': line.status,
                                               'new_status': new_status}
            msgs.append(msg)
            line.set_status(new_status)
        message = "\n".join(msgs)
        messages.info(request, message)
        order.notes.create(user=request.user, message=message,
                           note_type=OrderNote.SYSTEM)
        return self.reload_page()

    def create_shipping_event(self, request, order, lines, quantities):
        code = request.POST['shipping_event_type']
        try:
            event_type = ShippingEventType._default_manager.get(code=code)
        except ShippingEventType.DoesNotExist:
            messages.error(request, _("The event type '%s' is not valid")
                           % code)
            return self.reload_page()

        reference = request.POST.get('reference', None)
        try:
            EventHandler().handle_shipping_event(order, event_type, lines,
                                                 quantities,
                                                 reference=reference)
        except order_exceptions.InvalidShippingEvent as e:
            messages.error(request,
                           _("Unable to create shipping event: %s") % e)
        except order_exceptions.InvalidStatus as e:
            messages.error(request,
                           _("Unable to create shipping event: %s") % e)
        except PaymentError as e:
            messages.error(request, _("Unable to create shipping event due to"
                                      " payment error: %s") % e)
        else:
            messages.success(request, _("Shipping event created"))
        return self.reload_page()

    def create_payment_event(self, request, order, lines, quantities):
        """
        Create a payment event for a subset of order lines
        """
        amount_str = request.POST.get('amount', None)

        # If no amount passed, then we add up the total of the selected lines
        if not amount_str:
            amount = sum([line.line_price_incl_tax for line in lines])
        else:
            try:
                amount = D(amount_str)
            except InvalidOperation:
                messages.error(request, _("Please choose a valid amount"))
                return self.reload_page()

        return self._create_payment_event(request, order, amount, lines,
                                          quantities)

    def _create_payment_event(self, request, order, amount, lines=None,
                              quantities=None):
        code = request.POST.get('payment_event_type')
        try:
            event_type = PaymentEventType._default_manager.get(code=code)
        except PaymentEventType.DoesNotExist:
            messages.error(
                request, _("The event type '%s' is not valid") % code)
            return self.reload_page()
        try:
            EventHandler().handle_payment_event(
                order, event_type, amount, lines, quantities)
        except PaymentError as e:
            messages.error(request, _("Unable to create payment event due to"
                                      " payment error: %s") % e)
        except order_exceptions.InvalidPaymentEvent as e:
            messages.error(
                request, _("Unable to create payment event: %s") % e)
        else:
            messages.info(request, _("Payment event created"))
        return self.reload_page()


class LineDetailView(DetailView):
    """
    Dashboard view to show a single line of an order.
    Supports the permission-based dashboard.
    """
    model = Line
    context_object_name = 'line'
    template_name = 'dashboard/orders/line_detail.html'

    def get_object(self, queryset=None):
        order = get_order_for_user_or_404(self.request.user,
                                          self.kwargs['number'])
        try:
            return order.lines.get(pk=self.kwargs['line_id'])
        except self.model.DoesNotExist:
            raise Http404()

    def get_context_data(self, **kwargs):
        ctx = super(LineDetailView, self).get_context_data(**kwargs)
        ctx['order'] = self.object.order
        return ctx


def get_changes_between_models(model1, model2, excludes=None):
    """
    Return a dict of differences between two model instances
    """
    if excludes is None:
        excludes = []
    changes = {}
    for field in model1._meta.fields:
        if (isinstance(field, (fields.AutoField,
                               fields.related.RelatedField))
                or field.name in excludes):
            continue

        if field.value_from_object(model1) != field.value_from_object(model2):
            changes[field.verbose_name] = (field.value_from_object(model1),
                                           field.value_from_object(model2))
    return changes


def get_change_summary(model1, model2):
    """
    Generate a summary of the changes between two address models
    """
    changes = get_changes_between_models(model1, model2, ['search_text'])
    change_descriptions = []
    for field, delta in changes.items():
        change_descriptions.append(_("%(field)s changed from '%(old_value)s'"
                                     " to '%(new_value)s'")
                                   % {'field': field,
                                      'old_value': delta[0],
                                      'new_value': delta[1]})
    return "\n".join(change_descriptions)


class ShippingAddressUpdateView(UpdateView):
    """
    Dashboard view to update an order's shipping address.
    Supports the permission-based dashboard.
    """
    model = ShippingAddress
    context_object_name = 'address'
    template_name = 'dashboard/orders/shippingaddress_form.html'
    form_class = ShippingAddressForm

    def get_object(self, queryset=None):
        order = get_order_for_user_or_404(self.request.user,
                                          self.kwargs['number'])
        return get_object_or_404(self.model, order=order)

    def get_context_data(self, **kwargs):
        ctx = super(ShippingAddressUpdateView, self).get_context_data(**kwargs)
        ctx['order'] = self.object.order
        return ctx

    def form_valid(self, form):
        old_address = ShippingAddress.objects.get(id=self.object.id)
        response = super(ShippingAddressUpdateView, self).form_valid(form)
        changes = get_change_summary(old_address, self.object)
        if changes:
            msg = _("Delivery address updated:\n%s") % changes
            self.object.order.notes.create(user=self.request.user, message=msg,
                                           note_type=OrderNote.SYSTEM)
        return response

    def get_success_url(self):
        messages.info(self.request, _("Delivery address updated"))
        return reverse('dashboard:order-detail',
                       kwargs={'number': self.object.order.number, })
