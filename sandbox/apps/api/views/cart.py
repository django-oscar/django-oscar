"""
Basket of the mobile app (routed in apps/api/urls.py).

oscarapi's basket endpoints link products and lines by URL and do not check
the stock when a quantity changes, nor remove a voucher; these views answer
every change with the whole basket, priced by Oscar (strategy and offers):

    GET    cart/                     the basket
    POST   cart/lines/               {"product": <id>, "quantity": <n>}
    PATCH  cart/lines/<id>/          {"quantity": <n>} (0 removes the line)
    DELETE cart/lines/<id>/
    POST   cart/vouchers/            {"code": "<voucher code>"}
    DELETE cart/vouchers/<code>/

Signed-in users are identified by their DRF token; guests by Oscar's session
cookie (``sessionid``), and their basket is merged into the account's basket
when they come back with a token and the same cookie.
"""
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from oscar.apps.basket import signals
from oscar.core.loading import get_model
from oscarapi.basket import operations
from oscarapi.serializers.basket import VoucherAddSerializer
from rest_framework import authentication, permissions, serializers, status, views
from rest_framework.response import Response

from apps.api.mobile_serializers import MobileProductSerializer

Product = get_model("catalogue", "Product")


def get_cart(request):
    """The open basket of the request, priced; a guest basket kept in the
    session is merged into the account's basket"""
    guest_basket = (
        operations.get_anonymous_basket(request)
        if request.user.is_authenticated
        else None
    )
    basket = operations.get_basket(request, prepare=False)
    if guest_basket is not None and guest_basket.pk != basket.pk:
        basket.merge(guest_basket, add_quantities=True)
    # Not operations.prepare_basket(): it saves the session during the
    # request, which breaks when the request fails and its transaction is
    # rolled back. SessionMiddleware saves it once the response is ready.
    if request.user.is_authenticated:
        request.session.pop(settings.OSCAR_BASKET_COOKIE_OPEN, None)
    else:
        request.session[settings.OSCAR_BASKET_COOKIE_OPEN] = basket.pk
    return operations.assign_basket_strategy(basket, request)


def check_quantity(basket, product, quantity, line=None):
    """Raises a ValidationError with Oscar's message when the basket cannot
    hold ``quantity`` items of ``product`` (the new quantity of ``line``)"""
    # like Oscar's basket forms: the basket check takes the added quantity,
    # the stock check the quantity that would be bought
    allowed, message = basket.is_quantity_allowed(
        quantity - (line.quantity if line else 0), line=line
    )
    if allowed:
        info = basket.strategy.fetch_for_product(product)
        allowed, message = info.availability.is_purchase_permitted(quantity)
    if not allowed:
        raise serializers.ValidationError({"quantity": [message]})


def money(value):
    """Amounts as strings with 2 decimals, like the rest of the API"""
    return None if value is None else "%.2f" % value


def total(basket, name):
    """basket.total_incl_tax and co., excluding tax when it is unknown"""
    if basket.is_tax_known:
        return money(getattr(basket, name))
    return money(getattr(basket, name.replace("incl_tax", "excl_tax")))


class CartView(views.APIView):
    authentication_classes = (authentication.TokenAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def respond(self, request, basket=None, status_code=status.HTTP_200_OK):
        basket = basket or get_cart(request)
        # line prices and offers depend on the latest changes
        operations.apply_offers(request, basket)
        context = {"request": request, "strategy": basket.strategy}
        lines = basket.all_lines()
        data = {
            "id": basket.pk,
            "currency": basket.currency,
            "num_items": basket.num_items,
            "lines": [
                {
                    "id": line.pk,
                    "product": MobileProductSerializer(line.product, context=context).data,
                    "quantity": line.quantity,
                    "price_incl_tax": money(
                        line.line_price_incl_tax_incl_discounts
                        if basket.is_tax_known
                        else line.line_price_excl_tax_incl_discounts
                    ),
                    "price_incl_tax_excl_discounts": money(
                        line.line_price_incl_tax
                        if basket.is_tax_known
                        else line.line_price_excl_tax
                    ),
                    "warning": line.get_warning(),
                }
                for line in lines
            ],
            "total_incl_tax_excl_discounts": total(
                basket, "total_incl_tax_excl_discounts"
            ),
            "total_incl_tax": total(basket, "total_incl_tax"),
            "vouchers": [
                {
                    "code": discount["voucher"].code,
                    "name": discount["voucher"].name,
                    "amount": money(discount["discount"]),
                }
                for discount in basket.grouped_voucher_discounts
            ],
            "offers": [
                {"name": discount["name"], "amount": money(discount["discount"])}
                for discount in basket.offer_discounts
            ],
        }
        return Response(data, status=status_code)

    def get(self, request):
        return self.respond(request)


class _LineSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    product = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=0)


class CartLines(CartView):
    def post(self, request):
        data = _LineSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        if "product" not in data.validated_data:
            raise serializers.ValidationError({"product": [_("This field is required.")]})
        product = get_object_or_404(
            Product.objects.browsable(), pk=data.validated_data["product"]
        )
        quantity = max(data.validated_data["quantity"], 1)
        basket = get_cart(request)
        line = basket.lines.filter(product=product).first()
        check_quantity(
            basket, product, quantity + (line.quantity if line else 0), line=line
        )
        basket.add_product(product, quantity)
        return self.respond(request, basket, status.HTTP_201_CREATED)


class CartLineDetail(CartView):
    def get_line(self, basket, pk):
        return get_object_or_404(basket.lines, pk=pk)

    def patch(self, request, pk):
        data = _LineSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        basket = get_cart(request)
        line = self.get_line(basket, pk)
        quantity = data.validated_data["quantity"]
        if quantity == 0:
            line.delete()
        else:
            check_quantity(basket, line.product, quantity, line=line)
            line.quantity = quantity
            line.save()
        basket.reset_offer_applications()
        return self.respond(request, basket)

    def delete(self, request, pk):
        basket = get_cart(request)
        self.get_line(basket, pk).delete()
        basket.reset_offer_applications()
        return self.respond(request, basket)


class CartVouchers(CartView):
    def post(self, request):
        voucher_data = VoucherAddSerializer(
            data={"vouchercode": request.data.get("code", "")},
            context={"request": request},
        )
        if not voucher_data.is_valid():
            return Response(voucher_data.errors, status=status.HTTP_400_BAD_REQUEST)
        voucher = voucher_data.instance
        basket = get_cart(request)
        basket.vouchers.add(voucher)
        signals.voucher_addition.send(sender=None, basket=basket, voucher=voucher)
        operations.apply_offers(request, basket)
        if not any(
            discount["voucher"] == voucher for discount in basket.offer_applications
        ):
            basket.vouchers.remove(voucher)
            return Response(
                {
                    "non_field_errors": [
                        _("Your basket does not qualify for a voucher discount")
                    ]
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return self.respond(request, basket)


class CartVoucherDetail(CartView):
    def delete(self, request, code):
        basket = get_cart(request)
        voucher = get_object_or_404(basket.vouchers, code__iexact=code)
        basket.vouchers.remove(voucher)
        signals.voucher_removal.send(sender=None, basket=basket, voucher=voucher)
        basket.reset_offer_applications()
        return self.respond(request, basket)
