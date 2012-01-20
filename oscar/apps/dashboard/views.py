import csv

from django.views.generic import TemplateView, ListView
from django.contrib import messages
from django.utils.datastructures import SortedDict
from django.template.defaultfilters import date as format_date
from django.db.models.loading import get_model
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse

from oscar.apps.dashboard.forms import OrderSearchForm

Order = get_model('order', 'Order')


class IndexView(TemplateView):
    template_name = 'dashboard/index.html'


class OrderListView(ListView):
    model = Order
    context_object_name = 'orders'
    template_name = 'dashboard/orders/order_list.html'
    form_class = OrderSearchForm
    base_description = 'All orders'
    paginate_by = 25
    description = ''
    actions = ('download_selected_orders',)

    def get_queryset(self):
        """
        Build the queryset for this list and also update the title that 
        describes the queryset
        """
        queryset = self.model.objects.all().order_by('-date_placed')
        self.description = self.base_description

        if 'order_number' not in self.request.GET:
            self.form = self.form_class()
            return queryset

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data['order_number']:
            queryset = self.model.objects.filter(number__istartswith=data['order_number'])
            self.description = 'Orders with number starting with "%s"' % data['order_number']

        if data['name']:
            # If the value is two words, then assume they are first name and last name
            parts = data['name'].split()
            if len(parts) == 2:
                queryset = queryset.filter(Q(user__first_name__istartswith=parts[0]) |
                                           Q(user__last_name__istartswith=parts[1])).distinct()
            else:
                queryset = queryset.filter(Q(user__first_name__istartswith=data['name']) |
                                           Q(user__last_name__istartswith=data['name'])).distinct()
            self.description += " with customer name matching '%s'" % data['name']

        if data['product_title']:
            queryset = queryset.filter(lines__title__istartswith=data['product_title']).distinct()
            self.description += " including an item with title matching '%s'" % data['product_title']

        if data['product_id']:
            queryset = queryset.filter(Q(lines__upc=data['product_id']) |
                                       Q(lines__product_id=data['product_id'])).distinct()
            self.description += " including an item with ID '%s'" % data['product_id']

        if data['date_from'] and data['date_to']:
            # Add 24 hours to make search inclusive
            date_to = data['date_to'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_placed__gte=data['date_from']).filter(date_placed__lt=date_to)
            self.description += " placed between %s and %s" % (format_date(data['date_from']), format_date(data['date_to']))
        elif data['date_from']:
            queryset = queryset.filter(date_placed__gte=data['date_from'])
            self.description += " placed since %s" % format_date(data['date_from'])
        elif data['date_to']:
            date_to = data['date_to'] + datetime.timedelta(days=1)
            queryset = queryset.filter(date_placed__lt=date_to)
            self.description += " placed before %s" % format_date(data['date_to'])

        if data['voucher']:
            queryset = queryset.filter(discounts__voucher_code=data['voucher']).distinct()
            self.description += " using voucher '%s'" % data['voucher']

        if data['payment_method']:
            queryset = queryset.filter(sources__source_type__code=data['payment_method']).distinct()
            self.description += " paid for by %s" % data['payment_method']

        if data['status']:
            queryset = queryset.filter(status=data['status'])
            self.description += " with status %s" % data['status']

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

    def render_to_response(self, context):
        if self.is_csv_download():
            return self.download_selected_orders(self.request, context['object_list'])
        return super(OrderListView, self).render_to_response(context)

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', '').lower()
        if action not in self.actions:
            messages.error(self.request, "Invalid action")
            return HttpResponseRedirect(reverse('dashboard:orders'))
        order_ids = request.POST.getlist('selected_order')
        if not order_ids:
            messages.error(self.request, "You need to select some orders")
            return HttpResponseRedirect(reverse('dashboard:orders'))

        raw_orders = Order.objects.in_bulk(order_ids)
        orders = (raw_orders[int(id)] for id in order_ids)
        return getattr(self, action)(request, orders)

    def download_selected_orders(self, request, orders):
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=orders.csv'
        writer = csv.writer(response, delimiter=',')

        meta_data = (('number', 'Order number'),
                     ('value', 'Order value'),
                     ('date', 'Date of purchase'),
                     ('num_items', 'Number of items'),
                     ('status', 'Order status'),
                     ('shipping_address_name', 'Deliver to name'),
                     ('billing_address_name', 'Bill to name'),
                     )
        columns = SortedDict()
        for k,v in meta_data:
            columns[k] = v

        writer.writerow(columns.values())
        for order in orders:
            row = columns.copy()
            row['number'] = order.number
            row['value'] = order.total_incl_tax
            row['date'] = order.date_placed
            row['num_items'] = order.num_items
            row['status'] = order.status
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
