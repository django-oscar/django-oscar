from datetime import datetime
from decimal import Decimal as D

from django.views.generic import FormView
from django.db.models.loading import get_model
from django.db.models import Sum, Count

from oscar.apps.dashboard import forms

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Condition = get_model('offer', 'Condition')
Benefit = get_model('offer', 'Benefit')

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

    def get_current_offers(self):
        return ConditionalOffer.objects.filter(end_date__gt=datetime.now())

    def get_expired_offers(self):
        return ConditionalOffer.objects.filter(end_date__gt=datetime.now())

    def get_offer_conditions(self):
        conditions = {}
        for id_, _ in Condition.TYPE_CHOICES:
            conditions[id_] = Condition.objects.filter(type=id_)
        return conditions

    def get_offer_benefits(self):
        benefits = {}
        for id_, _ in Benefit.TYPE_CHOICES:
            benefits[id_] = Benefit.objects.filter(type=id_)
        return benefits 

    def get_stats(self, filters):
        orders = Order.objects.filter(**filters)
        open_alerts = StockAlert.objects.filter(status=StockAlert.OPEN)
        closed_alerts = StockAlert.objects.filter(status=StockAlert.CLOSED)

        self.get_offer_conditions()

        stats = {
            'total_products': Product.objects.count(),
            'total_open_stock_alerts': open_alerts.count(),
            'total_closed_stock_alerts': closed_alerts.count(),
            'total_current_offers': self.get_current_offers().count(),
            'total_current_conditions': self.get_offer_conditions(),
            'total_current_benefits': self.get_offer_benefits(),
            #'total_expired_offers': self.get_expired_offers().count(),

            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),
            'total_revenue': orders.aggregate(Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'order_status_breakdown': orders.order_by('status').values('status').annotate(freq=Count('id'))
        }
        return stats
