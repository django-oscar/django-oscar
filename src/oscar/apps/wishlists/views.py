from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from oscar.core.loading import get_model

WishList = get_model('wishlists', 'WishList')


class WishListView(DetailView):
    template_name = 'oscar/wishlists/wishlist_detail.html'
    model = WishList
    context_object_name = 'wishlist'

    def dispatch(self, request, *args, **kwargs):
        wishlist = self.get_object()

        if wishlist.is_allowed_to_see(request.user):
            return super().dispatch(request, *args, **kwargs)
        elif (
            wishlist.visibility == WishList.PRIVATE
            or request.user.is_authenticated
            and not wishlist.is_allowed_to_see(request.user)
        ):
            raise PermissionDenied
        else:
            messages.info(request, _("You must be logged in to view the wish list"))
            redirect_url = "%s?next=%s" % (settings.LOGIN_URL, request.path)
            return redirect(redirect_url)

    def get_object(self, queryset=None):
        return get_object_or_404(WishList, key=self.kwargs.get("key"))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        wishlist_lines = self.object.lines.filter(product__isnull=False)
        paginator = Paginator(wishlist_lines, settings.OSCAR_PRODUCTS_PER_PAGE)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        ctx["wishlist_title"] = str(self.object)
        ctx["page_obj"] = page_obj
        ctx["paginator"] = paginator

        return ctx
