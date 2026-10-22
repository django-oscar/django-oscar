import copy
import hashlib
import time

from django.contrib import messages
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBase, JsonResponse, QueryDict
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.encoding import smart_str
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from django.conf import settings

from oscar.core.utils import safe_referrer


def _prune_expired_bulk_intermediate_buckets(session, session_key, ttl_seconds):
    """
    Drop pending bulk-action buckets older than ttl_seconds, so an abandoned
    action (never confirmed or cancelled) doesn't sit in the session forever.
    """
    buckets = session.get(session_key, {})
    if not buckets:
        return buckets
    cutoff = time.time() - ttl_seconds
    expired = [
        token for token, data in buckets.items() if data.get("created_at", 0) < cutoff
    ]
    for token in expired:
        del buckets[token]
    if expired:
        session.modified = True
    return buckets


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
            response = action_handler.execute(request, objects)
        else:
            response = getattr(self, action)(request, objects)

        if isinstance(response, HttpResponseBase):
            return response

        return redirect(self.get_success_url(request))

    def get_objects(self, ids):
        return self.get_queryset().filter(pk__in=ids)


class BulkSelection:
    """
    The objects a pending two-step bulk action applies to.

    A selection is the path and query string of the list view it was made on, so
    it takes the same space in the session whether it holds ten objects or a
    million.
    When the user ticked objects on the list, ``ids`` narrows the query to those.

    To notice when the selection changed before it is executed, we keep what
    the user last saw: ``count`` always, and for a ticked selection also
    ``fingerprint``, the sorted ids that were present. Comparing the count is
    enough for a select-across selection (it may hold any number of objects, so
    recording every id is not affordable, and it really means "everything
    matching the filter"), but a ticked selection compares the ids themselves,
    so a change that leaves the count the same -- one object drops out as
    another reappears -- is still caught.
    """

    def __init__(
        self,
        action,
        path=None,
        query="",
        ids=None,
        count=0,
        created_at=None,
        fingerprint=None,
    ):
        self.action = action
        self.path = path
        self.query = query
        self.ids = ids
        self.count = count
        self.fingerprint = fingerprint
        self.created_at = time.time() if created_at is None else created_at

    def to_session(self):
        return {
            "action": self.action,
            "path": self.path,
            "query": self.query,
            "ids": self.ids,
            "count": self.count,
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
        }

    @classmethod
    def from_session(cls, data):
        if "object_ids" in data:
            # stored before selections were queries
            return cls(
                data.get("action"),
                ids=data["object_ids"],
                count=len(data["object_ids"]),
                fingerprint=sorted(data["object_ids"]),
                created_at=data.get("created_at"),
            )
        return cls(
            data.get("action"),
            path=data.get("path"),
            query=data.get("query", ""),
            ids=data.get("ids"),
            count=data.get("count", 0),
            fingerprint=data.get("fingerprint"),
            created_at=data.get("created_at"),
        )

    def get_token(self):
        """
        A short token identifying this pending action + selection.

        Each pending action is stored under its own session bucket keyed by
        this token, so concurrent tabs don't overwrite each other's selection.
        """
        ids = "*" if self.ids is None else ",".join(str(pk) for pk in sorted(self.ids))
        raw = "%s:%s:%s:%s" % (self.action, self.path, self.query, ids)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


class IntermediateBulkEditMixin(BulkEditMixin):
    """
    Extension of BulkEditMixin
    Allows for bulk actions with an intermediate step that contains a form.
    So the user can input extra parameters to the bulk action.

    Actions with an intermediate step should be specified by
    putting the keys from actions into intermediate_actions

    The selection is stored as the list's query, see ``BulkSelection``. The
    intermediate view gets the objects back from this view through
    ``get_bulk_selection_queryset``, so all filtering of the list applies.
    """

    intermediate_actions = {}
    bulk_intermediate_session_key = settings.OSCAR_BULK_INTERMEDIATE_SESSION_KEY
    bulk_intermediate_token_param = settings.OSCAR_BULK_INTERMEDIATE_TOKEN_PARAM
    bulk_intermediate_ttl_seconds = settings.OSCAR_BULK_INTERMEDIATE_SESSION_TTL_SECONDS

    # the most objects a selection may hold, None for no limit. Ticked objects
    # need no limit of their own: they are at most one page of the list.
    max_bulk_selection = getattr(settings, "OSCAR_MAX_BULK_SELECTION", None)

    # query parameters of the list that don't change which objects it holds
    bulk_selection_ignored_params = ("page",)

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

    def get_bulk_selection_query(self, request):
        query = request.GET.copy()
        for param in self.bulk_selection_ignored_params:
            query.pop(param, None)
        return query.urlencode()

    @classmethod
    def get_bulk_selection_queryset(cls, request, selection):
        """
        The objects in ``selection``, as ``request.user`` sees them now on the
        list with the selection's query.
        """
        list_request = copy.copy(request)
        list_request.method = "GET"
        list_request.GET = QueryDict(selection.query)
        list_request.POST = QueryDict()
        view = cls()
        view.setup(list_request)
        if selection.ids is None:
            return view.get_select_across_queryset()
        return view.get_selected_queryset(selection.ids)

    def get_selected_queryset(self, ids):
        """The ticked objects ``ids`` that are on the list."""
        return self.get_select_across_queryset().filter(pk__in=ids)

    def _too_many_error(self, request, count, limit):
        messages.error(
            request,
            _(
                "Too many %(object)ss selected (%(count)d). Narrow your"
                " selection to %(limit)d or fewer and try again."
            )
            % {
                "object": self.get_checkbox_object_name(),
                "count": count,
                "limit": limit,
            },
        )
        return redirect(self.get_error_url(request))

    def _handle_intermediate_action(self, request, action, *args, **kwargs):
        selection = BulkSelection(
            action, path=request.path, query=self.get_bulk_selection_query(request)
        )

        select_across = request.POST.get(self.select_across_param, "").lower()
        if select_across != "1":
            selection.ids = self.get_selected_ids(request)

        queryset = self.get_bulk_selection_queryset(request, selection)
        if selection.ids is None:
            # select-across: track only the size, the set may be unbounded
            selection.count = queryset.count()
        else:
            # ticked: remember exactly which objects are selected, so the
            # confirmation step can tell the set apart, not only its size
            selection.fingerprint = sorted(queryset.values_list("pk", flat=True))
            selection.count = len(selection.fingerprint)

        if not selection.count:
            messages.error(
                request,
                _("You need to select some %ss") % self.get_checkbox_object_name(),
            )
            return redirect(self.get_error_url(request))

        if (
            self.max_bulk_selection is not None
            and selection.count > self.max_bulk_selection
        ):
            return self._too_many_error(
                request, selection.count, self.max_bulk_selection
            )

        token = selection.get_token()
        _prune_expired_bulk_intermediate_buckets(
            request.session,
            self.bulk_intermediate_session_key,
            self.bulk_intermediate_ttl_seconds,
        )
        buckets = request.session.setdefault(self.bulk_intermediate_session_key, {})
        buckets[token] = selection.to_session()
        request.session.modified = True

        url = self.get_intermediate_url(request, action)
        return redirect("%s?%s=%s" % (url, self.bulk_intermediate_token_param, token))


class IntermediateBulkActionView(View):
    """
    Generic view for the confirmation step of a two-step bulk action.
    Pair with ``IntermediateBulkEditMixin`` on the originating list view.

    Reads the pending action and selection from the session, renders
    the action's template with its form on GET, and dispatches to
    ``execute_action`` on POST.

    When the number of selected objects changed since the user last saw it,
    a GET shows a message, and a POST shows the page again instead of
    executing, so the user confirms what is actually selected.

    The selected objects are found again through the list view the selection
    was made on, see ``get_list_view_class``.

    Subclasses must implement ``get_cancel_url``, ``get_success_url`` and
    ``get_objects``.
    """

    intermediate_actions = {}
    bulk_intermediate_session_key = "bulk_intermediate"
    bulk_intermediate_token_param = "key"
    bulk_intermediate_ttl_seconds = 60 * 60 * 24

    #: the list view the selection was made on, used to resolve it again
    list_view_class = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._action = None
        self._token = None
        self.selection = None
        self._selection_queryset = None
        self._selection_count = None

    def dispatch(self, request, *args, **kwargs):
        self._token = request.GET.get(self.bulk_intermediate_token_param)
        buckets = request.session.get(self.bulk_intermediate_session_key, {})
        session_data = buckets.get(self._token) if self._token else None
        if session_data is not None:
            # Actively using this pending action right now: refresh it so it
            # isn't pruned as abandoned just because time has passed since
            # it was created.
            session_data["created_at"] = time.time()
            request.session.modified = True
        _prune_expired_bulk_intermediate_buckets(
            request.session,
            self.bulk_intermediate_session_key,
            self.bulk_intermediate_ttl_seconds,
        )
        if session_data is not None:
            self.selection = BulkSelection.from_session(session_data)
            self._action = self.selection.action
        if (
            self.selection is None
            or not self._action
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

    def get_list_view_class(self):
        """The list view the selection was made on."""
        if self.list_view_class is None:
            raise ImproperlyConfigured(
                "%s must set list_view_class" % type(self).__name__
            )
        return self.list_view_class

    def get_selection_queryset(self):
        """The selected objects, as they are now."""
        if self._selection_queryset is None:
            self._selection_queryset = (
                self.get_list_view_class().get_bulk_selection_queryset(
                    self.request, self.selection
                )
            )
        return self._selection_queryset

    def get_selection_count(self):
        if self._selection_count is None:
            self._selection_count = self.get_selection_queryset().count()
        return self._selection_count

    def selection_changed(self):
        """
        Whether the selection changed since the user last saw it. What was seen
        is stored, so the next page compares against this one.

        A select-across selection compares only the count: it may hold any
        number of objects, so recording every id is not affordable, and it
        really means "everything matching the filter", recomputed on apply. A
        ticked selection compares the ids themselves, so a change that leaves
        the count the same -- one object drops out as another reappears -- is
        still caught.
        """
        if self.selection.ids is None:
            return self._count_changed()
        return self._membership_changed()

    def _count_changed(self):
        count = self.get_selection_count()
        if count == self.selection.count:
            return False
        self._selection_changed_message(self.selection.count, count)
        self.selection.count = count
        self._save_selection()
        return True

    def _membership_changed(self):
        present = sorted(self.get_selection_queryset().values_list("pk", flat=True))
        if self.selection.fingerprint is None:
            # stored before fingerprints existed, adopt what is there as the
            # baseline without warning
            self.selection.fingerprint = present
            self.selection.count = len(present)
            self._save_selection()
            return False
        if present == self.selection.fingerprint:
            return False
        self._selection_changed_message(len(self.selection.fingerprint), len(present))
        self.selection.fingerprint = present
        self.selection.count = len(present)
        self._save_selection()
        return True

    def _selection_changed_message(self, old_count, new_count):
        messages.warning(
            self.request,
            _(
                "The selection changed since it was made: it held %(old)d"
                " items and now holds %(new)d. Check the selection before you"
                " continue."
            )
            % {"old": old_count, "new": new_count},
        )

    def _save_selection(self):
        buckets = self.request.session.get(self.bulk_intermediate_session_key, {})
        buckets[self._token] = self.selection.to_session()
        self.request.session[self.bulk_intermediate_session_key] = buckets
        self.request.session.modified = True

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
            "selection_count": self.get_selection_count(),
            "selection_is_across": self.selection.ids is None,
        }
        ctx.update(action.get_context())
        ctx.update(kwargs)
        return ctx

    def get_template_name(self):
        return self.intermediate_actions[self._action].template

    def get(self, request, *args, **kwargs):
        self.selection_changed()
        return TemplateResponse(
            request, self.get_template_name(), self.get_context_data()
        )

    def post(self, request, *args, **kwargs):
        if self.selection_changed():
            # never execute on a selection the user hasn't seen
            return redirect(request.get_full_path())
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
