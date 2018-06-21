import json
from datetime import timedelta
from decimal import Decimal as D
from decimal import ROUND_UP

from django.db.models import Avg, Count, Sum
from django.template.response import TemplateResponse
from django.utils.timezone import now
from django.views.generic import TemplateView

from oscar.apps.promotions.models import AbstractPromotion
from oscar.core.compat import get_user_model
from oscar.core.loading import get_class, get_model

RelatedFieldWidgetWrapper = get_class('dashboard.widgets', 'RelatedFieldWidgetWrapper')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
Voucher = get_model('voucher', 'Voucher')
Basket = get_model('basket', 'Basket')
StockAlert = get_model('partner', 'StockAlert')
Product = get_model('catalogue', 'Product')
Order = get_model('order', 'Order')
Line = get_model('order', 'Line')
User = get_user_model()


class IndexView(TemplateView):
    """
    An overview view which displays several reports about the shop.

    Supports the permission-based dashboard. It is recommended to add a
    index_nonstaff.html template because Oscar's default template will
    display potentially sensitive store information.
    """

    def get_template_names(self):
        if self.request.user.is_staff:
            return ['dashboard/index.html', ]
        else:
            return ['dashboard/index_nonstaff.html', 'dashboard/index.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(self.get_stats())
        return ctx

    def get_active_site_offers(self):
        """
        Return active conditional offers of type "site offer". The returned
        ``Queryset`` of site offers is filtered by end date greater then
        the current date.
        """
        return ConditionalOffer.objects.filter(
            end_datetime__gt=now(), offer_type=ConditionalOffer.SITE)

    def get_active_vouchers(self):
        """
        Get all active vouchers. The returned ``Queryset`` of vouchers
        is filtered by end date greater then the current date.
        """
        return Voucher.objects.filter(end_datetime__gt=now())

    def get_number_of_promotions(self, abstract_base=AbstractPromotion):
        """
        Get the number of promotions for all promotions derived from
        *abstract_base*. All subclasses of *abstract_base* are queried
        and if another abstract base class is found this method is executed
        recursively.
        """
        total = 0
        for cls in abstract_base.__subclasses__():
            if cls._meta.abstract:
                total += self.get_number_of_promotions(cls)
            else:
                total += cls.objects.count()
        return total

    def get_open_baskets(self, filters=None):
        """
        Get all open baskets. If *filters* dictionary is provided they will
        be applied on all open baskets and return only filtered results.
        """
        if filters is None:
            filters = {}
        filters['status'] = Basket.OPEN
        return Basket.objects.filter(**filters)

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
        # Get datetime for 24 hours agao
        time_now = now().replace(minute=0, second=0)
        start_time = time_now - timedelta(hours=hours - 1)

        orders_last_day = Order.objects.filter(date_placed__gt=start_time)

        order_total_hourly = []
        for hour in range(0, hours, 2):
            end_time = start_time + timedelta(hours=2)
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
        divisor = 1
        while divisor < max_value / 50:
            divisor *= 10
        max_value = (max_value / divisor).quantize(D('1'), rounding=ROUND_UP)
        max_value *= divisor
        if max_value:
            segment_size = (max_value) / D('100.0')
            for item in order_total_hourly:
                item['percentage'] = int(item['total_incl_tax'] / segment_size)

            y_range = []
            y_axis_steps = max_value / D(str(segments))
            for idx in reversed(range(segments + 1)):
                y_range.append(idx * y_axis_steps)
        else:
            y_range = []
            for item in order_total_hourly:
                item['percentage'] = 0

        ctx = {
            'order_total_hourly': order_total_hourly,
            'max_revenue': max_value,
            'y_range': y_range,
        }
        return ctx

    def get_stats(self):
        datetime_24hrs_ago = now() - timedelta(hours=24)

        orders = Order.objects.all()
        orders_last_day = orders.filter(date_placed__gt=datetime_24hrs_ago)

        open_alerts = StockAlert.objects.filter(status=StockAlert.OPEN)
        closed_alerts = StockAlert.objects.filter(status=StockAlert.CLOSED)

        total_lines_last_day = Line.objects.filter(
            order__in=orders_last_day).count()
        stats = {
            'total_orders_last_day': orders_last_day.count(),
            'total_lines_last_day': total_lines_last_day,

            'average_order_costs': orders_last_day.aggregate(
                Avg('total_incl_tax')
            )['total_incl_tax__avg'] or D('0.00'),

            'total_revenue_last_day': orders_last_day.aggregate(
                Sum('total_incl_tax')
            )['total_incl_tax__sum'] or D('0.00'),

            'hourly_report_dict': self.get_hourly_report(hours=24),
            'total_customers_last_day': User.objects.filter(
                date_joined__gt=datetime_24hrs_ago,
            ).count(),

            'total_open_baskets_last_day': self.get_open_baskets({
                'date_created__gt': datetime_24hrs_ago
            }).count(),

            'total_products': Product.objects.count(),
            'total_open_stock_alerts': open_alerts.count(),
            'total_closed_stock_alerts': closed_alerts.count(),

            'total_site_offers': self.get_active_site_offers().count(),
            'total_vouchers': self.get_active_vouchers().count(),
            'total_promotions': self.get_number_of_promotions(),

            'total_customers': User.objects.count(),
            'total_open_baskets': self.get_open_baskets().count(),
            'total_orders': orders.count(),
            'total_lines': Line.objects.count(),
            'total_revenue': orders.aggregate(
                Sum('total_incl_tax')
            )['total_incl_tax__sum'] or D('0.00'),

            'order_status_breakdown': orders.order_by(
                'status'
            ).values('status').annotate(freq=Count('id'))
        }
        return stats


class PopUpWindowCreateUpdateMixin(object):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if (RelatedFieldWidgetWrapper.TO_FIELD_VAR in self.request.GET or
                RelatedFieldWidgetWrapper.TO_FIELD_VAR in self.request.POST):
            to_field = self.request.GET.get(RelatedFieldWidgetWrapper.TO_FIELD_VAR,
                                            self.request.POST.get(RelatedFieldWidgetWrapper.TO_FIELD_VAR))
            ctx['to_field'] = to_field
            ctx['to_field_var'] = RelatedFieldWidgetWrapper.TO_FIELD_VAR

        if (RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.GET or
                RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.POST):
            is_popup = self.request.GET.get(RelatedFieldWidgetWrapper.IS_POPUP_VAR,
                                            self.request.POST.get(RelatedFieldWidgetWrapper.IS_POPUP_VAR))
            ctx['is_popup'] = is_popup
            ctx['is_popup_var'] = RelatedFieldWidgetWrapper.IS_POPUP_VAR

        return ctx

    def forms_valid(self, form, formset):
        # So that base view classes can do pop-up window specific things, like
        # not displaying notification messages using the messages framework
        self.is_popup = False
        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.POST:
            self.is_popup = True

        return super().forms_valid(form, formset)


class PopUpWindowCreateMixin(PopUpWindowCreateUpdateMixin):

    # form_valid and form_invalid are called, depending on the validation
    # result of just the form, and return a redirect to the success URL or
    # redisplay the form, respectively. In both cases we need to check our
    # formsets as well, so both methods should do the same.
    # If both the form and formset are valid, then they should call
    # forms_valid, which should be defined in the base view class, to in
    # addition save the formset, and return a redirect to the success URL.
    def forms_valid(self, form, formset):
        response = super().forms_valid(form, formset)

        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.POST:
            obj = form.instance
            to_field = self.request.POST.get(RelatedFieldWidgetWrapper.TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = obj._meta.pk.attname
            value = obj.serializable_value(attr)
            popup_response_data = json.dumps({
                'value': str(value),
                'obj': str(obj),
            })
            return TemplateResponse(self.request, 'dashboard/widgets/popup_response.html', {
                'popup_response_data': popup_response_data,
            })

        else:
            return response


class PopUpWindowUpdateMixin(PopUpWindowCreateUpdateMixin):

    # form_valid and form_invalid are called, depending on the validation
    # result of just the form, and return a redirect to the success URL or
    # redisplay the form, respectively. In both cases we need to check our
    # formsets as well, so both methods should do the same.
    # If both the form and formset are valid, then they should call
    # forms_valid, which should be defined in the base view class, to in
    # addition save the formset, and return a redirect to the success URL.
    def forms_valid(self, form, formset):
        response = super().forms_valid(form, formset)

        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.POST:
            obj = form.instance
            opts = obj._meta
            to_field = self.request.POST.get(RelatedFieldWidgetWrapper.TO_FIELD_VAR)
            if to_field:
                attr = str(to_field)
            else:
                attr = opts.pk.attname
            # Retrieve the `object_id` from the resolved pattern arguments.
            value = self.request.resolver_match.kwargs['pk']
            new_value = obj.serializable_value(attr)
            popup_response_data = json.dumps({
                'action': 'change',
                'value': str(value),
                'obj': str(obj),
                'new_value': str(new_value),
            })
            return TemplateResponse(self.request, 'dashboard/widgets/popup_response.html', {
                'popup_response_data': popup_response_data,
            })

        else:
            return response


class PopUpWindowDeleteMixin(object):

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.GET:
            ctx['is_popup'] = self.request.GET.get(RelatedFieldWidgetWrapper.IS_POPUP_VAR)
            ctx['is_popup_var'] = RelatedFieldWidgetWrapper.IS_POPUP_VAR

        return ctx

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL, or closes the popup, it it is one.
        """
        # So that base view classes can do pop-up window specific things, like
        # not displaying notification messages using the messages framework
        self.is_popup = False
        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in self.request.POST:
            self.is_popup = True

        obj = self.get_object()

        response = super().delete(request, *args, **kwargs)

        if RelatedFieldWidgetWrapper.IS_POPUP_VAR in request.POST:
            obj_id = obj.pk
            popup_response_data = json.dumps({
                'action': 'delete',
                'value': str(obj_id),
            })
            return TemplateResponse(request, 'dashboard/widgets/popup_response.html', {
                'popup_response_data': popup_response_data,
            })

        else:
            return response
