# pylint: disable=attribute-defined-outside-init
import datetime
from decimal import Decimal as D
from decimal import InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, fields
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, ListView, UpdateView

from oscar.apps.payment.exceptions import PaymentError
from oscar.core.compat import UnicodeCSVWriter
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime
from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin

Student = get_model("school", "Student")
StudentSearchForm = get_class("dashboard.students.forms", "StudentSearchForm")


def queryset_students_for_user(user):
    """
    Returns a queryset of all students that a user is allowed to access.
    A staff user may access all students.
    To allow access to an student for a non-staff user, school has to have the user.
    """
    queryset = Student._default_manager.prefetch_related("parent",)
    if user.is_staff:
        return queryset
    else:
        return queryset.filter(school__user=user)


def get_student_for_user_or_404(user, national_id):
    try:
        return queryset_students_for_user(user).get(national_id=national_id)
    except ObjectDoesNotExist:
        raise Http404()





class StudentListView(BulkEditMixin, ListView):
    """
    Dashboard view for a list of students.
    Supports the permission-based dashboard.
    """

    model = Student
    context_object_name = "students"
    template_name = "oscar/dashboard/students/student_list.html"
    form_class = StudentSearchForm
    paginate_by = settings.OSCAR_DASHBOARD_ITEMS_PER_PAGE
    actions = ("download_selected_students", "change_student_statuses",)
    CSV_COLUMNS = {
        "national_id": _("National ID"),
        "full_name_en": _("Full Name (English)"),
        "full_name_ar": _("Full Name (Arabic)"),
        "date_of_birth": _("Date of Birth"),
        "grade": _("Grade"),
        "status": _("status"),
        "parent": _("Parent email address"),
    }

    def dispatch(self, request, *args, **kwargs):
        # base_queryset is equal to all students the user is allowed to access
        self.base_queryset = queryset_students_for_user(request.user).order_by(
            "national_id"
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        if (
            "national_id" in request.GET
            and request.GET.get("response_format", "html") == "html"
        ):
            # Redirect to Student detail page if valid student national_id is given
            try:
                student = self.base_queryset.get(national_id=request.GET["national_id"])
            except Student.DoesNotExist:
                pass
            else:
                return redirect("dashboard:student-detail", national_id=student.national_id)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Build the queryset for this list.
        """
        queryset = sort_queryset(
            self.base_queryset, self.request, ["national_id"]
        )

        self.form = self.form_class(self.request.GET)
        if not self.form.is_valid():
            return queryset

        data = self.form.cleaned_data

        if data["national_id"]:
            queryset = self.base_queryset.filter(
                national_id__istartswith=data["national_id"]
            )

        if data.get("full_name_en"):
            queryset = queryset.filter(full_name_en__istartswith=data["full_name_en"]).distinct()

        if data.get("full_name_ar"):
            queryset = queryset.filter(full_name_ar__istartswith=data["full_name_ar"]).distinct()


        if data["grade"]:
            queryset = queryset.filter(grade__istartswith=data["grade"])

        if data["birth_date_from"] and data["birth_date_to"]:
            birth_date_to = datetime_combine(data["birth_date_to"], datetime.time.max)
            birth_date_from = datetime_combine(data["birth_date_from"], datetime.time.min)
            queryset = queryset.filter(
                date_of_birth__gte=birth_date_from, date_of_birth__lt=birth_date_to
            )
        elif data["birth_date_from"]:
            birth_date_from = datetime_combine(data["birth_date_from"], datetime.time.min)
            queryset = queryset.filter(date_of_birth__gte=birth_date_from)
        elif data["birth_date_to"]:
            birth_date_to = datetime_combine(data["birth_date_to"], datetime.time.max)
            queryset = queryset.filter(date_of_birth__lt=birth_date_to)

        if data.get("status"):
            queryset = queryset.filter(is_active=data["status"])

        if data["parent"]:
            queryset = queryset.filter(parent__user__email=data["parent"])

        return queryset

    def get_search_filter_descriptions(self):
        """Describe the filters used in the search.

        These are user-facing messages describing what filters
        were used to filter students in the search query.

        Returns:
            list of unicode messages

        """
        descriptions = []

        # Attempt to retrieve data from the submitted form
        # If the form hasn't been submitted, then `cleaned_data`
        # won't be set, so default to None.
        data = getattr(self.form, "cleaned_data", None)

        if data is None:
            return descriptions

        if data.get("national_id"):
            descriptions.append(
                _('Student national_id starts with "{national_id}"').format(
                    national_id=data["national_id"]
                )
            )

        if data.get("full_name_en"):
            descriptions.append(
                _('Student full name in English starts with "{full_name_en}"').format(
                    full_name_en=data["full_name_en"]
                )
            )
        if data.get("full_name_ar"):
            descriptions.append(
                _('Student full name in Arabic starts with "{full_name_ar}"').format(
                    full_name_ar=data["full_name_ar"]
                )
            )
        if data.get("grade"):
            descriptions.append(
                _('Student  grade starts with "{grade}"').format(
                    grade=data["grade"]
                )
            )

        if data.get("parent"):
            descriptions.append(
                # Translators: "UPC" means "universal product code" and it is
                # used to uniquely identify a product in an online store.
                # "Item" in this context means an item in an student placed
                # in an online store.
                _('Owns by parent with email "{parent}"').format(parent=data["parent"])
            )


        if data.get("birth_date_from") and data.get("birth_date_to"):
            descriptions.append(
                # Translators: This string refers to students in an online
                # store that were made within a particular date range.
                _("The date of birth is between {start_date} and {end_date}").format(
                    start_date=data["birth_date_from"], end_date=data["birth_date_to"]
                )
            )

        elif data.get("birth_date_from"):
            descriptions.append(
                # Translators: This string refers to students in an online store
                # that were made after a particular date.
                _("The date of birth after {start_date}").format(start_date=data["birth_date_from"])
            )

        elif data.get("birth_date_to"):
            end_date = data["birth_date_to"] + datetime.timedelta(days=1)
            descriptions.append(
                # Translators: This string refers to students in an online store
                # that were made before a particular date.
                _("The date of birth before {end_date}").format(end_date=end_date)
            )

        if data.get("status"):
            descriptions.append(
                # Translators: This string refers to an student in an
                # online store.  Some examples of student status are
                # "purchased", "cancelled", or "refunded".
                _("Student status is {student_status}").format(student_status="Active" if data["status"] else "Inactive")
            )

        return descriptions

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = self.form
        ctx["search_filters"] = self.get_search_filter_descriptions()
        return ctx

    def is_csv_download(self):
        return self.request.GET.get("response_format", None) == "csv"

    def get_paginate_by(self, queryset):
        return None if self.is_csv_download() else self.paginate_by

    def render_to_response(self, context, **response_kwargs):
        if self.is_csv_download():
            return self.download_selected_students(self.request, context["object_list"])
        return super().render_to_response(context, **response_kwargs)

    def get_download_filename(self, request):
        return "students.csv"

    def get_row_values(self, student):
        row = {
        "national_id": student.national_id,
        "full_name_en": student.full_name_en,
        "full_name_ar": student.full_name_ar,
        "date_of_birth": format_datetime(student.date_of_birth, "DATETIME_FORMAT"),
        "grade": student.grade,
        "status":"Active" if student.is_active else "Inactive",
    }
        if student.parent:
            row["parent"] = student.parent.user.email
        return row

    def download_selected_students(self, request, students):
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            "attachment; filename=%s" % self.get_download_filename(request)
        )
        writer = UnicodeCSVWriter(open_file=response)

        writer.writerow(self.CSV_COLUMNS.values())
        for student in students:
            row_values = self.get_row_values(student)
            writer.writerow([row_values.get(column, "") for column in self.CSV_COLUMNS])
        return response

    def change_student_statuses(self, request, students):
        for student in students:
            self.change_student_status(request, student)
        return redirect("dashboard:students-list")

    def change_student_status(self, request, student):
        action = request.POST.get("perform_action", None)
        print("action", action)
        if action == "active":
            student.is_active = True
            student.save()
        elif action == "inactive":
            student.is_active = False
            student.save()
        elif action == "delete":
            student.delete()

 

class StudentDetailView(DetailView):
    """
    Dashboard view to display a single student.

    Supports the permission-based dashboard.
    """

    model = Student
    context_object_name = "student"
    template_name = "oscar/dashboard/students/student_detail.html"

    # These strings are method names that are allowed to be called from a
    # submitted form.
    student_actions = (
        "delete_student",
        "change_student_status",
    )

    def get_object(self, queryset=None):
        return get_student_for_user_or_404(self.request.user, self.kwargs["national_id"])

    def post(self, request, *args, **kwargs):
        # For POST requests, we use a dynamic dispatch technique where a
        # parameter specifies what we're trying to do with the form submission.
        # We distinguish between student-level actions and line-level actions.

        student = self.object = self.get_object()

        # Look for student-level action first
        if "student_action" in request.POST:
            return self.handle_student_action(
                request, student, request.POST["student_action"]
            )

        return self.reload_page(error=_("No valid action submitted"))

    def handle_student_action(self, request, student, action):
        if action not in self.student_actions:
            return self.reload_page(error=_("Invalid action"))
        return getattr(self, action)(request, student)

    def reload_page(self, fragment=None, error=None):
        url = reverse("dashboard:student-detail", kwargs={"national_id": self.object.national_id})
        if fragment:
            url += "#" + fragment
        if error:
            messages.error(self.request, error)
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_tab"] = kwargs.get("active_tab", "lines")
        return ctx






    def delete_student(self, request, student):
        try:
            student = student.get(national_id=request.POST.get("national_id", None))
        except ObjectDoesNotExist:
            messages.error(request, _("Student cannot be deleted"))
        else:
            student.delete()
            messages.info(request, _("Student deleted Successfully"))
        return self.reload_page()

    def change_student_status(self, request, student):
        old_status = "Active" if student.is_active else "Inactive"
        new_status = "Inactive" if student.is_active else "Active"
        if student.is_active:
            student.is_active = False
        else:
            student.is_active = True
        success_msg = _(
            "Student status changed from '%(old_status)s' to '%(new_status)s'"
        ) % {"old_status": old_status, "new_status": new_status}
        return self.reload_page()

    def create_student_payment_event(self, request, student):
        """
        Create a payment event for the whole student
        """
        amount_str = request.POST.get("amount", None)
        try:
            amount = D(amount_str)
        except InvalidOperation:
            messages.error(request, _("Please choose a valid amount"))
            return self.reload_page()
        return self._create_payment_event(request, student, amount)


class StudentUpdateView(UpdateView):
    """
    Dashboard view to update student details.
    Supports the permission-based dashboard.
    """
    model = Student
    context_object_name = 'student'
    template_name = 'oscar/dashboard/students/student_update.html'
    # You'll need to create this form class
    form_class = get_class('dashboard.students.forms', 'StudentForm')
    
    def get_object(self, queryset=None):
        """
        Ensures users can only edit students they have permission to access
        """
        return get_student_for_user_or_404(self.request.user, self.kwargs['national_id'])
    
    def get_success_url(self):
        """
        Redirects to the student detail page after successful update
        """
        messages.success(self.request, _("Student details updated successfully"))
        return reverse('dashboard:student-detail', kwargs={'national_id': self.object.national_id})
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = _('Update student: %s') % self.object.full_name_en
        return ctx
    
    def form_valid(self, form):
        """
        Save the form and record any changes in the audit log
        """
        # Get a copy of the student before updating
        old_student = get_student_for_user_or_404(self.request.user, self.kwargs['national_id'])
        
        # Save the changes
        response = super().form_valid(form)
        
        # Get change summary
        changes = get_change_summary(old_student, self.object)
        
        if changes:
            msg = _("Fields updated: %s") % changes
            messages.info(self.request, msg)
        
        return response

    def form_invalid(self, form):
        """
        Handle invalid form submissions
        """
        messages.error(self.request, _("Your submitted data was not valid - please correct the errors below"))
        return super().form_invalid(form)