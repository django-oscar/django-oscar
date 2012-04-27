from decimal import Decimal as D
from datetime import datetime, timedelta

from django.views.generic import FormView
from django.db.models.loading import get_model
from django.db.models import Avg, Sum, Count

from oscar.apps.dashboard import forms
from oscar.apps.offer.models import SITE

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Voucher = get_model('voucher', 'Voucher')

StockAlert = get_model('partner', 'StockAlert')
Product = get_model('catalogue', 'Product')

Order = get_model('order', 'Order')
Line = get_model('order', 'Line')


class IndexView(FormView):
    template_name = 'dashboard/index.html'
    form_class = forms.OrderSummaryForm

    def get(self, request, *args, **kwargs):
        if 'date_from' in request.GET or 'date_to' in request.GET:
            return self.post(request, *args, **kwargs)
        return super(IndexView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        ctx = self.get_context_data(form=form,
                                    filters=form.get_filters())
        return self.render_to_response(ctx)

    def get_form_kwargs(self):
        kwargs = super(IndexView, self).get_form_kwargs()
        kwargs['data'] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        filters = kwargs.get('filters', {})
        ctx.update(self.get_stats(filters))
        return ctx

    def get_site_offers(self):
        return ConditionalOffer.objects.filter(end_date__gt=datetime.now(),
                                               offer_type=SITE)

    def get_vouchers(self):
        return Voucher.objects.filter(end_date__gt=datetime.now())

    def get_bar_chart_data(self, hours=25):
        time_now = datetime.now().replace(minute=0, second=0)
        # subtract 1 to make sure that the full hour is taken into account
        start_time = time_now - timedelta(hours=hours-1)

        orders_last_day = Order.objects.filter(date_placed__gt=start_time)

        order_total_per_hour = []
        for hour in range(0, hours):
            end_time = start_time + timedelta(hours=1)

            hourly_orders = orders_last_day.filter(date_placed__gt=start_time, date_placed__lt=end_time)
            total = hourly_orders.aggregate(Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.0')

            order_total_per_hour.append({'end_time': end_time, 'total_incl_tax': total})
            start_time = end_time

        max_value = max([x['total_incl_tax'] for x in order_total_per_hour])

        for item in order_total_per_hour:
            item['percentage'] = int(item['total_incl_tax'] / (max_value / D(100.)))

        return {
            'order_total_per_hour': order_total_per_hour,
            'max_revenue': max_value,
            'y_range': [int(x) for x in reversed(range(0, max_value, (max_value/D(10))))]
        }

    def get_stats(self, filters):
        orders = Order.objects.filter(**filters)

        date_24hrs_ago = datetime.now() - timedelta(hours=24)
        orders_last_day = Order.objects.filter(date_placed__gt=date_24hrs_ago)

        open_alerts = StockAlert.objects.filter(status=StockAlert.OPEN)
        closed_alerts = StockAlert.objects.filter(status=StockAlert.CLOSED)

        stats = {
            'total_orders_last_day': orders_last_day.count(),
            'average_order_costs': orders_last_day.aggregate(Avg('total_incl_tax'))['total_incl_tax__avg'] or D('0.00'),
            'total_revenue_last_day': orders_last_day.aggregate(Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),

            'bar_chart_data': self.get_bar_chart_data(),

            'total_products': Product.objects.count(),
            'total_open_stock_alerts': open_alerts.count(),
            'total_closed_stock_alerts': closed_alerts.count(),

            'total_site_offers': self.get_site_offers().count(),
            'total_vouchers': self.get_vouchers().count(),

            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),
            'total_revenue': orders.aggregate(Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'order_status_breakdown': orders.order_by('status').values('status').annotate(freq=Count('id'))
        }
        return stats
