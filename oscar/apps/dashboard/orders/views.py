import datetime
from decimal import Decimal as D, InvalidOperation

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.loading import get_model
from django.db.models import fields, Q, Sum, Count
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import date as format_date
from django.utils.datastructures import SortedDict
from django.views.generic import ListView, DetailView, UpdateView, FormView
from django.conf import settings

from oscar.core.loading import get_class
from oscar.apps.dashboard.orders import forms
from oscar.views.generic import BulkEditMixin
from oscar.apps.dashboard.reports.csv_utils import CsvUnicodeWriter
from oscar.apps.payment.exceptions import PaymentError
from oscar.apps.order.exceptions import InvalidShippingEvent, InvalidStatus

Order = get_model('order', 'Order')
OrderNote = get_model('order', 'OrderNote')
ShippingAddress = get_model('order', 'ShippingAddress')
Line = get_model('order', 'Line')
ShippingEventType = get_model('order', 'ShippingEventType')
PaymentEventType = get_model('order', 'PaymentEventType')
EventHandler = get_class('order.processing', 'EventHandler')


class OrderStatsView(FormView):
    template_name = 'dashboard/orders/statistics.html'
    form_class = forms.OrderStatsForm

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
        orders = Order.objects.filter(**filters)
        stats = {
            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),
            'total_revenue': orders.aggregate(
                Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'order_status_breakdown': orders.order_by('status').values(
                'status').annotate(freq=Count('id'))
        }
        return stats


class OrderListView(ListView, BulkEditMixin):
    model = Order
    context_object_name = 'orders'
    template_name = 'dashboard/orders/order_list.html'
    form_class = forms.OrderSearchForm
    desc_template = _("%(main_filter)s %(name_filter)s %(title_filter)s"
                      "%(upc_filter)s %(sku_filter)s %(date_filter)s"
                      "%(voucher_filter)s %(payment_filter)s %(status_filter)s")
    paginate_by = 25
    description = ''
    actions = ('download_selected_orders',)
    current_view = 'dashboard:order-list'

    def get(self, request, *args, **kwargs):
        if 'order_number' in request.GET and request.GET.get('response_format', 'html') == 'html':
            try:
                order = Order.objects.get(number=request.GET['order_number'])
            except Order.DoesNotExist:
                pass
            else:
                return HttpResponseRedirect(reverse('dashboard:order-detail', kwargs={'number': order.number}))
        return super(OrderListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build the queryset for this list and also update the title that
        describes the queryset
        """
        queryset = self.model.objects.all().order_by('-date_placed')
        queryset = self.sort_queryset(queryset)
        desc_ctx = {
            'main_filter': _('All orders'),
            'name_filter': '',
            'title_filter': '',
            'upc_filter': '',
            'sku_filter': '',
            'date_filter': '',
            'voucher_filter': '',
            'payment_filter': '',
            'status_filter': '',
        }

        # Look for shortcut query filters
        if 'order_status' in self.request.GET:
            self.form = self.form_class()
            status = self.request.GET['order_status']
            if status.lower() == 'none':
                desc_ctx['main_filter'] = _("Orders without an order status")
                status = None
            else:
                desc_ctx['main_filter'] = _("Orders with status '%s'") % status
            self.description = self.desc_template % desc_ctx
            return self.model.objects.filter(status=status)

        if 'order_number' not in self.request.GET:
            self.description = self.desc_template % desc_ctx
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['order_number']:
            queryset = self.model.objects.filter(number__istartswith=data['order_number'])
            desc_ctx['main_filter'] = _('Orders with number starting with "%s"') % data['order_number']

        if data['name']:
            # If the value is two words, then assume they are first name and last name
            parts = data['name'].split()
            allow_anon = getattr(settings, 'OSCAR_ALLOW_ANON_CHECKOUT', False)

            if len(parts) == 1:
                parts = [data['name'], data['name']]
            else:
                parts = [parts[0], parts[1:]]

            filter = Q(user__first_name__istartswith=parts[0]) |\
                     Q(user__last_name__istartswith=parts[1])
            if allow_anon:
                filter |= Q(billing_address__first_name__istartswith=parts[0]) |\
                          Q(shipping_address__first_name__istartswith=parts[0]) |\
                          Q(billing_address__last_name__istartswith=parts[1]) |\
                          Q(shipping_address__last_name__istartswith=parts[1])

            queryset = queryset.filter(filter).distinct()
            desc_ctx['name_filter'] = _(" with customer name matching '%s'") % data['name']

        if data['product_title']:
            queryset = queryset.filter(lines__title__istartswith=data['product_title']).distinct()
            desc_ctx['title_filter'] = _(" including an item with title matching '%s'") % data['product_title']

        if data['upc']:
            queryset = queryset.filter(lines__upc=data['upc'])
            desc_ctx['upc_filter'] = _(" including an item with UPC '%s'") % data['upc']

        if data['partner_sku']:
            queryset = queryset.filter(lines__partner_sku=data['partner_sku'])
            desc_ctx['upc_filter'] = _(" including an item with ID '%s'") % data['partner_sku']

        if data['date_from'] and data['date_to']:
            # Add 24 hours to make search inclusive
            date_to = data['date_to'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_placed__gte=data['date_from']).filter(date_placed__lt=date_to)
            desc_ctx['date_filter'] = _(" placed between %(start_date)s and %(end_date)s") % {
                'start_date': format_date(data['date_from']),
                'end_date': format_date(data['date_to'])}
        elif data['date_from']:
            queryset = queryset.filter(date_placed__gte=data['date_from'])
            desc_ctx['date_filter'] = _(" placed since %s") % format_date(data['date_from'])
        elif data['date_to']:
            date_to = data['date_to'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_placed__lt=date_to)
            desc_ctx['date_filter'] = _(" placed before %s") % format_date(data['date_to'])

        if data['voucher']:
            queryset = queryset.filter(discounts__voucher_code=data['voucher']).distinct()
            desc_ctx['voucher_filter'] = _(" using voucher '%s'") % data['voucher']

        if data['payment_method']:
            queryset = queryset.filter(sources__source_type__code=data['payment_method']).distinct()
            desc_ctx['payment_filter'] = _(" paid for by %s") % data['payment_method']

        if data['status']:
            queryset = queryset.filter(status=data['status'])
            desc_ctx['status_filter'] = _(" with status %s") % data['status']

        self.description = self.desc_template % desc_ctx
        return queryset

    def sort_queryset(self, queryset):
        sort = self.request.GET.get('sort', None)
        allowed_sorts = ['number',]
        if sort in allowed_sorts:
            direction = self.request.GET.get('dir', 'desc')
            sort = ('-' if direction == 'desc' else '') + sort
            queryset = queryset.order_by(sort)
        return queryset

    def get_context_data(self, **kwargs):
        ctx = super(OrderListView, self).get_context_data(**kwargs)
        ctx['queryset_description'] = self.description
        ctx['form'] = self.form
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
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % self.get_download_filename(request)
        writer = CsvUnicodeWriter(response, delimiter=',')

        meta_data = (('number', _('Order number')),
                     ('value', _('Order value')),
                     ('date', _('Date of purchase')),
                     ('num_items', _('Number of items')),
                     ('status', _('Order status')),
                     ('customer', _('Customer email address')),
                     ('shipping_address_name', _('Deliver to name')),
                     ('billing_address_name', _('Bill to name')),
                     )
        columns = SortedDict()
        for k, v in meta_data:
            columns[k] = v

        writer.writerow(columns.values())
        for order in orders:
            row = columns.copy()
            row['number'] = order.number
            row['value'] = order.total_incl_tax
            row['date'] = format_date(order.date_placed, 'DATETIME_FORMAT')
            row['num_items'] = order.num_items
            row['status'] = order.status
            row['customer'] = order.email
            if order.shipping_address:
                row['shipping_address_name'] = order.shipping_address.name()
            else:
                row['shipping_address_name'] = ''
            if order.billing_address:
                row['billing_address_name'] = order.billing_address.name()
            else:
                row['billing_address_name'] = ''

            encoded_values = [unicode(value).encode('utf8') for value in row.values()]
            writer.writerow(encoded_values)
        return response


class OrderDetailView(DetailView):
    model = Order
    context_object_name = 'order'
    template_name = 'dashboard/orders/order_detail.html'
    order_actions = ('save_note', 'delete_note', 'change_order_status',
                     'create_order_payment_event')
    line_actions = ('change_line_statuses', 'create_shipping_event',
                    'create_payment_event')

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, number=self.kwargs['number'])

    def get_context_data(self, **kwargs):
        ctx = super(OrderDetailView, self).get_context_data(**kwargs)
        ctx['active_tab'] = kwargs.get('active_tab', 'lines')
        ctx['note_form'] = self.get_order_note_form()
        ctx['line_statuses'] = Line.all_statuses()
        ctx['shipping_event_types'] = ShippingEventType.objects.all()
        ctx['payment_event_types'] = PaymentEventType.objects.all()
        return ctx

    def get_order_note_form(self):
        post_data = None
        kwargs = {}
        if self.request.method == 'POST':
            post_data = self.request.POST
        note_id = self.kwargs.get('note_id', None)
        if note_id:
            note = get_object_or_404(OrderNote, order=self.object, id=note_id)
            if note.is_editable():
                kwargs['instance'] = note
        return forms.OrderNoteForm(post_data, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        order = self.object

        # Look for order-level action
        order_action = request.POST.get('order_action', '').lower()
        if order_action:
            if order_action not in self.order_actions:
                messages.error(self.request, _("Invalid action"))
                return self.reload_page_response()
            else:
                return getattr(self, order_action)(request, order)

        # Look for line-level action
        line_action = request.POST.get('line_action', '').lower()
        if line_action:
            if line_action not in self.line_actions:
                messages.error(self.request, "Invalid action")
                return self.reload_page_response()
            else:
                line_ids = request.POST.getlist('selected_line')
                line_quantities = []
                for line_id in line_ids:
                    qty = request.POST.get('selected_line_qty_%s' % line_id)
                    line_quantities.append(int(qty))
                lines = order.lines.filter(id__in=line_ids)
                if lines.count() == 0:
                    messages.error(self.request, _("You must select some lines to act on"))
                    return self.reload_page_response()
                return getattr(self, line_action)(request, order, lines, line_quantities)

        messages.error(request, _("No valid action submitted"))
        return self.reload_page_response()

    def reload_page_response(self, fragment=None):
        url = reverse('dashboard:order-detail', kwargs={'number': self.object.number})
        if fragment:
            url += '#' + fragment
        return HttpResponseRedirect(url)

    def save_note(self, request, order):
        form = self.get_order_note_form()
        success_msg = _("Note saved")
        if form.is_valid():
            note = form.save(commit=False)
            note.user = request.user
            note.order = order
            note.save()
            messages.success(self.request, success_msg)
            return self.reload_page_response(fragment='notes')
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
        return self.reload_page_response()

    def change_order_status(self, request, order):
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid") % new_status)
            return self.reload_page_response()
        if not new_status in order.available_statuses():
            messages.error(request, _("The new status '%s' is not valid for this order") % new_status)
            return self.reload_page_response()

        handler = EventHandler()
        try:
            handler.handle_order_status_change(order, new_status)
        except PaymentError, e:
            messages.error(request, _("Unable to change order status due to payment error: %s") % e)
        else:
            msg = _("Order status changed from '%(old_status)s' to '%(new_status)s'") % {
                'old_status': order.status,
                'new_status': new_status}
            messages.info(request, msg)
            order.notes.create(user=request.user, message=msg,
                            note_type=OrderNote.SYSTEM)
        return self.reload_page_response(fragment='activity')

    def change_line_statuses(self, request, order, lines, quantities):
        new_status = request.POST['new_status'].strip()
        if not new_status:
            messages.error(request, _("The new status '%s' is not valid") % new_status)
            return self.reload_page_response()
        errors = []
        for line in lines:
            if new_status not in line.available_statuses():
                errors.append(_("'%(status)s' is not a valid new status for line %(line_id)d") % {
                    'status': new_status,
                    'line_id': line.id})
        if errors:
            messages.error(request, "\n".join(errors))
            return self.reload_page_response()

        msgs = []
        for line in lines:
            msg = _("Status of line #%(line_id)d changed from '%(old_status)s' to '%(new_status)s'") % {
                        'line_id': line.id,
                        'old_status': line.status,
                        'new_status': new_status}
            msgs.append(msg)
            line.set_status(new_status)
        message = "\n".join(msgs)
        messages.info(request, message)
        order.notes.create(user=request.user, message=message,
                           note_type=OrderNote.SYSTEM)
        return self.reload_page_response()

    def create_shipping_event(self, request, order, lines, quantities):
        code = request.POST['shipping_event_type']
        try:
            event_type = ShippingEventType._default_manager.get(code=code)
        except ShippingEventType.DoesNotExist:
            messages.error(request, _("The event type '%s' is not valid") % code)
            return self.reload_page_response()

        reference = request.POST.get('reference', None)
        try:
            EventHandler().handle_shipping_event(order, event_type, lines,
                                                 quantities,
                                                 reference=reference)
        except InvalidShippingEvent, e:
            messages.error(request, _("Unable to create shipping event: %s") % e)
        except InvalidStatus, e:
            messages.error(request, _("Unable to create shipping event: %s") % e)
        except PaymentError, e:
            messages.error(request, _("Unable to create shipping event due to payment error: %s") % e)
        else:
            messages.success(request, _("Shipping event created"))
        return self.reload_page_response()

    def create_order_payment_event(self, request, order):
        amount_str = request.POST.get('amount', None)
        try:
            amount = D(amount_str)
        except InvalidOperation:
            messages.error(request, _("Please choose a valid amount"))
            return self.reload_page_response()
        return self._create_payment_event(request, order, amount)

    def _create_payment_event(self, request, order, amount, lines=None,
                              quantities=None):
        code = request.POST['payment_event_type']
        try:
            event_type = PaymentEventType._default_manager.get(code=code)
        except PaymentEventType.DoesNotExist:
            messages.error(request, _("The event type '%s' is not valid") % code)
            return self.reload_page_response()
        try:
            EventHandler().handle_payment_event(order, event_type, amount,
                                                lines, quantities)
        except PaymentError, e:
            messages.error(request, _("Unable to change order status due to payment error: %s") % e)
        else:
            messages.info(request, _("Payment event created"))
        return self.reload_page_response()

    def create_payment_event(self, request, order, lines, quantities):
        amount_str = request.POST.get('amount', None)

        # If no amount passed, then we add up the total of the selected lines
        if not amount_str:
            amount = D('0.00')
            for line, quantity in zip(lines, quantities):
                amount += int(quantity) * line.line_price_incl_tax
        else:
            try:
                amount = D(amount_str)
            except InvalidOperation:
                messages.error(request, _("Please choose a valid amount"))
                return self.reload_page_response()

        return self._create_payment_event(request, order, amount, lines,
                                          quantities)


class LineDetailView(DetailView):
    model = Line
    context_object_name = 'line'
    template_name = 'dashboard/orders/line_detail.html'

    def get_object(self, queryset=None):
        try:
            return self.model.objects.get(pk=self.kwargs['line_id'])
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
        if not (isinstance(field, (fields.AutoField, fields.related.RelatedField))
                or field.name in excludes):
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
        change_descriptions.append(_("%(field)s changed from '%(old_value)s' to '%(new_value)s'") % {
            'field': field,
            'old_value': delta[0],
            'new_value': delta[1]})
    return "\n".join(change_descriptions)


class ShippingAddressUpdateView(UpdateView):
    model = ShippingAddress
    context_object_name = 'address'
    template_name = 'dashboard/orders/shippingaddress_form.html'
    form_class = forms.ShippingAddressForm

    def get_object(self, queryset=None):
        return get_object_or_404(self.model, order__number=self.kwargs['number'])

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
        return reverse('dashboard:order-detail', kwargs={'number': self.object.order.number, })
