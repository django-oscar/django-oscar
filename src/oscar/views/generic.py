import hashlib

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View

from oscar.core.utils import safe_referrer


class AbstractBulkAction:
    label = ""

    def __str__(self):
        return str(self.label)


class BulkAction(AbstractBulkAction):
    """Base class for bulk actions. Intended to be used with BulkEditMixin."""

    def execute(self, request, objects):
        raise NotImplementedError


class IntermediateBulkAction(AbstractBulkAction):
    """Base class for two-step bulk actions. Intended to be used with IntermediateBulkEditMixin."""

    form_class = None
    template = "oscar/dashboard/intermediate_bulk_action.html"
    # Whether the confirmation page should require ticking an "this cannot be
    # undone" checkbox before the form can be submitted.
    require_irreversible_confirmation = False

    def get_context(self):
        return {}

    def execute(self, request, objects, form):
        raise NotImplementedError


class PostActionMixin:
    """
    Simple mixin to forward POST request that contain a key 'action'
    onto a method of form "do_{action}".

    This only works with DetailView
    """

    def post(self, request, *args, **kwargs):
        if "action" in self.request.POST:
            model = self.get_object()
            # The do_* method is required to do what it needs to with the model
            # it is passed, and then to assign the HTTP response to
            # self.response.
            method_name = "do_%s" % self.request.POST["action"].lower()
            if hasattr(self, method_name):
                getattr(self, method_name)(model)
                return self.response
            else:
                messages.error(request, _("Invalid form submission"))
                return self.get(request, *args, **kwargs)

        # There may be no fallback implementation at super().post
        try:
            return super().post(request, *args, **kwargs)
        except AttributeError:
            messages.error(request, _("Invalid form submission"))
            return self.get(request, *args, **kwargs)


class BulkEditMixin:
    """
    Mixin for views that have a bulk editing facility.  This is normally in the
    form of tabular data where each row has a checkbox.  The UI allows a number
    of rows to be selected and then some 'action' to be performed on them.

    actions should be a dict with "action_name": BulkAction().
    """

    action_param = "action"
    select_across_param = "select_across"

    actions: dict[str, BulkAction] = None
    checkbox_object_name = None

    def get_actions(self):
        base = self.actions or {}
        if isinstance(base, (tuple, list)):
            base = dict.fromkeys(base)
        return base

    def get_checkbox_object_name(self):
        if self.checkbox_object_name:
            return self.checkbox_object_name
        return smart_str(self.model._meta.object_name.lower())

    def get_error_url(self, request):
        return safe_referrer(request, ".")

    def get_success_url(self, request):
        return safe_referrer(request, ".")

    def get_select_across_queryset(self):
        return self.get_queryset()

    def get_selected_ids(self, request):
        """
        Return the selected object IDs from the request.
        """
        select_across = request.POST.get(self.select_across_param, "").lower()

        if select_across == "1":
            return list(self.get_select_across_queryset().values_list("pk", flat=True))

        posted_ids = request.POST.getlist(f"selected_{self.get_checkbox_object_name()}")

        return list(
            self.get_queryset().filter(pk__in=posted_ids).values_list("pk", flat=True)
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get(self.action_param, "").lower()
        actions = self.get_actions()

        if not actions or action not in actions:
            messages.error(self.request, _("Invalid action"))
            return redirect(self.get_error_url(request))

        ids = self.get_selected_ids(request)

        if not ids:
            messages.error(
                self.request,
                _("You need to select some %ss") % self.get_checkbox_object_name(),
            )
            return redirect(self.get_error_url(request))

        objects = self.get_objects(ids)

        action_handler = actions[action]

        if hasattr(action_handler, "execute"):
            action_handler.execute(request, objects)
        else:
            getattr(self, action)(request, objects)

        return redirect(self.get_success_url(request))

    def get_objects(self, ids):
        object_dict = self.get_object_dict(ids)
        return [object_dict[id] for id in ids if id in object_dict]

    def get_object_dict(self, ids):
        return self.get_queryset().in_bulk(ids)


class IntermediateBulkEditMixin(BulkEditMixin):
    """
    Extension of BulkEditMixin
    Allows for bulk actions with an intermediate step that contains a form.
    So the user can input extra parameters to the bulk action.

    Actions with an intermediate step should be specified by
    putting the keys from actions into intermediate_actions
    """

    intermediate_actions = {}
    bulk_intermediate_session_key = "bulk_intermediate"
    bulk_intermediate_token_param = "key"

    def get_intermediate_url(self, request, action):
        raise NotImplementedError(
            "Subclasses of IntermediateBulkEditMixin must "
            "implement get_intermediate_url()"
        )

    def post(self, request, *args, **kwargs):
        action = request.POST.get(self.action_param, "").lower()

        if action in self.intermediate_actions:
            return self._handle_intermediate_action(request, action, *args, **kwargs)

        return super().post(request, *args, **kwargs)

    def get_bulk_intermediate_token(self, action, object_ids):
        """
        Return a short token identifying this pending action + selection.

        Each pending action is stored under its own session bucket keyed by
        this token, so concurrent tabs don't overwrite each other's selection.
        """
        raw = "%s:%s" % (action, ",".join(str(pk) for pk in sorted(object_ids)))
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def _handle_intermediate_action(self, request, action, *args, **kwargs):
        object_ids = self.get_selected_ids(request)

        if not object_ids:
            messages.error(
                request,
                _("You need to select some %ss") % self.get_checkbox_object_name(),
            )
            return redirect(self.get_error_url(request))

        token = self.get_bulk_intermediate_token(action, object_ids)
        buckets = request.session.setdefault(self.bulk_intermediate_session_key, {})
        buckets[token] = {"object_ids": object_ids, "action": action}
        request.session.modified = True

        url = self.get_intermediate_url(request, action)
        return redirect("%s?%s=%s" % (url, self.bulk_intermediate_token_param, token))


class IntermediateBulkActionView(View):
    """
    Generic view for the confirmation step of a two-step bulk action.
    Pair with ``IntermediateBulkEditMixin`` on the originating list view.

    Reads the pending action and selected IDs from the session, renders
    the action's template with its form on GET, and dispatches to
    ``execute_action`` on POST.

    Subclasses must implement ``get_cancel_url``, ``get_success_url`` and ``get_objects``.
    """

    intermediate_actions = {}
    bulk_intermediate_session_key = "bulk_intermediate"
    bulk_intermediate_token_param = "key"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._action = None
        self._selected_ids = []
        self._token = None

    def dispatch(self, request, *args, **kwargs):
        self._token = request.GET.get(self.bulk_intermediate_token_param)
        buckets = request.session.get(self.bulk_intermediate_session_key, {})
        session_data = buckets.get(self._token, {}) if self._token else {}
        self._action = session_data.get("action")
        self._selected_ids = session_data.get("object_ids", [])
        if (
            not self._action
            or not self._selected_ids
            or self._action not in self.intermediate_actions
        ):
            messages.warning(
                request,
                _("No pending bulk action. Please select items and try again."),
            )
            return redirect(self.get_cancel_url())
        return super().dispatch(request, *args, **kwargs)

    def get_cancel_url(self):
        raise NotImplementedError

    def get_success_url(self):
        raise NotImplementedError

    def get_form_kwargs(self):
        return {}

    def get_form(self, data=None):
        action = self.intermediate_actions[self._action]
        return action.form_class(data=data, **self.get_form_kwargs())

    def get_context_data(self, form=None, **kwargs):
        if form is None:
            form = self.get_form()
        action = self.intermediate_actions[self._action]
        ctx = {
            "form": form,
            "action": self._action,
            "action_label": action.label,
            "cancel_url": self.get_cancel_url(),
            "require_irreversible_confirmation": action.require_irreversible_confirmation,
        }
        ctx.update(action.get_context())
        ctx.update(kwargs)
        return ctx

    def get_template_name(self):
        return self.intermediate_actions[self._action].template

    def get(self, request, *args, **kwargs):
        return TemplateResponse(
            request, self.get_template_name(), self.get_context_data()
        )

    def post(self, request, *args, **kwargs):
        form = self.get_form(data=request.POST)
        if not form.is_valid():
            return TemplateResponse(
                request, self.get_template_name(), self.get_context_data(form=form)
            )
        self.execute_action(request, form)
        self._clear_session(request)
        return redirect(self.get_success_url())

    def get_objects(self, form):
        raise NotImplementedError

    def execute_action(self, request, form):
        action = self.intermediate_actions[self._action]
        return action.execute(request, self.get_objects(form), form)

    def _clear_session(self, request):
        buckets = request.session.get(self.bulk_intermediate_session_key, {})
        if self._token in buckets:
            del buckets[self._token]
            request.session.modified = True


class ObjectLookupView(View):
    """Base view for json lookup for objects"""

    def get_queryset(self):
        return self.model.objects.all()  # pylint: disable=E1101

    def format_object(self, obj):
        return {
            "id": obj.pk,
            "text": str(obj),
        }

    def initial_filter(self, qs, value):
        return qs.filter(pk__in=value.split(","))

    # pylint: disable=unused-argument
    def lookup_filter(self, qs, term):
        return qs

    def paginate(self, qs, page, page_limit):
        total = qs.count()

        start = (page - 1) * page_limit
        stop = start + page_limit

        qs = qs[start:stop]

        return qs, (page_limit * page < total)

    def get_args(self):
        GET = self.request.GET
        return (
            GET.get("initial", None),
            GET.get("q", None),
            int(GET.get("page", 1)),
            int(GET.get("page_limit", 20)),
        )

    # pylint: disable=W0201
    def get(self, request):
        self.request = request
        qs = self.get_queryset()

        initial, q, page, page_limit = self.get_args()

        if initial:
            qs = self.initial_filter(qs, initial)
            more = False
        else:
            if q:
                qs = self.lookup_filter(qs, q)
            qs, more = self.paginate(qs, page, page_limit)

        return JsonResponse(
            {
                "results": [self.format_object(obj) for obj in qs],
                "pagination": {"more": more},
            }
        )
