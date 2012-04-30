from decimal import Decimal as D
from datetime import datetime, timedelta

from django.views.generic import TemplateView
from django.db.models.loading import get_model
from django.db.models import Avg, Sum, Count

from oscar.core.loading import get_class
from oscar.apps.offer.models import SITE
OrderSummaryForm = get_class('dashboard.forms', 'OrderSummaryForm')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Voucher = get_model('voucher', 'Voucher')
StockAlert = get_model('partner', 'StockAlert')
Product = get_model('catalogue', 'Product')
Order = get_model('order', 'Order')
Line = get_model('order', 'Line')


class IndexView(TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(IndexView, self).get_context_data(**kwargs)
        ctx.update(self.get_stats())
        return ctx

    def get_active_site_offers(self):
        """
        Return active conditional offers of type "site offer". The returned
        ``Queryset`` of site offers is filtered by end date greater then 
        the current date.
        """
        return ConditionalOffer.objects.filter(end_date__gt=datetime.now(),
                                               offer_type=SITE)

    def get_active_vouchers(self):
        """
        Get all active vouchers. The returned ``Queryset`` of vouchers 
        is filtered by end date greater then the current date.
        """
        return Voucher.objects.filter(end_date__gt=datetime.now())

    def get_hourly_report(self, hours=24, segments=10):
        """
        Get report of order revenue split up in hourly chunks. A report is
        generated for the last *hours* (default=24) from the current time. 
        The report provides ``max_revenue`` of the hourly order revenue sum,
        ``y-range`` as the labeling for the y-axis in a template and
        ``order_total_hourly``, a list of properties for hourly chunks.
        *segments* defines the number of labeling segments used for the y-axis
        when generating the y-axis labels (default=10).
        """
        # create report by the full hour
        time_now = datetime.now().replace(minute=0, second=0)
        # subtract 1 to make sure that the full hour is taken into account
        start_time = time_now - timedelta(hours=hours-1)

        orders_last_day = Order.objects.filter(date_placed__gt=start_time)

        order_total_hourly = []
        for hour in range(0, hours):
            end_time = start_time + timedelta(hours=1)

            hourly_orders = orders_last_day.filter(date_placed__gt=start_time,
                                                   date_placed__lt=end_time)
            total = hourly_orders.aggregate(
                Sum('total_incl_tax')
            )['total_incl_tax__sum'] or D('0.0')

            order_total_hourly.append({
                'end_time': end_time,
                'total_incl_tax': total
            })

            start_time = end_time

        max_value = max([x['total_incl_tax'] for x in order_total_hourly])

        if max_value:
            segment_size = (max_value) / D(100.)
            for item in order_total_hourly:
                item['percentage'] = int(item['total_incl_tax'] / segment_size)

            y_range = []
            y_axis_steps = max_value / D(segments)
            for idx in reversed(range(segments+1)):
                y_range.append(idx * y_axis_steps)
        else:
            y_range = []
            for item in order_total_hourly:
                item['percentage'] = 0

        return {
            'order_total_hourly': order_total_hourly,
            'max_revenue': max_value,
            'y_range': y_range,
        }

    def get_stats(self):
        orders = Order.objects.filter()

        date_24hrs_ago = datetime.now() - timedelta(hours=24)
        orders_last_day = Order.objects.filter(date_placed__gt=date_24hrs_ago)

        open_alerts = StockAlert.objects.filter(status=StockAlert.OPEN)
        closed_alerts = StockAlert.objects.filter(status=StockAlert.CLOSED)

        stats = {
            'total_orders_last_day': orders_last_day.count(),

            'total_lines_last_day': orders_last_day.aggregate(
                Sum('lines')
            )['lines__sum'] or 0,

            'average_order_costs': orders_last_day.aggregate(
                Avg('total_incl_tax')
            )['total_incl_tax__avg'] or D('0.00'),

            'total_revenue_last_day': orders_last_day.aggregate(
                Sum('total_incl_tax')
            )['total_incl_tax__sum'] or D('0.00'),

            'hourly_report_dict': self.get_hourly_report(hours=24),
            'total_products': Product.objects.count(),
            'total_open_stock_alerts': open_alerts.count(),
            'total_closed_stock_alerts': closed_alerts.count(),
            'total_site_offers': self.get_active_site_offers().count(),
            'total_vouchers': self.get_active_vouchers().count(),

            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),

            'total_revenue': orders.aggregate(
                Sum('total_incl_tax')
            )['total_incl_tax__sum'] or D('0.00'),

            'order_status_breakdown': orders.order_by(
                'status'
            ).values('status').annotate(freq=Count('id'))
        }
        return stats
