from decimal import Decimal as D

from django.views.generic import FormView
from django.db.models.loading import get_model
from django.db.models import Sum, Count

from oscar.apps.dashboard import forms

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

    def get_stats(self, filters):
        orders = Order.objects.filter(**filters)
        stats = {
            'total_orders': orders.count(),
            'total_lines': Line.objects.filter(order__in=orders).count(),
            'total_revenue': orders.aggregate(Sum('total_incl_tax'))['total_incl_tax__sum'] or D('0.00'),
            'order_status_breakdown': orders.order_by('status').values('status').annotate(freq=Count('id'))
        }
        return stats
