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
from django.views.generic import DetailView, FormView, ListView, UpdateView, CreateView

from oscar.apps.payment.exceptions import PaymentError
from oscar.core.compat import UnicodeCSVWriter
from oscar.core.loading import get_class, get_model
from oscar.core.utils import datetime_combine, format_datetime

from oscar.views import sort_queryset
from oscar.views.generic import BulkEditMixin
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView
from django.core.files.storage import default_storage
import csv
from io import TextIOWrapper

Student = get_model("school", "Student")
StudentSearchForm = get_class("dashboard.students.forms", "StudentSearchForm")
StudentImportValidator = get_class("dashboard.students.validators", "StudentImportValidator")


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
        "gender": _("Gender"),
        "parent_phone_number": _("Parent Phone Number"),
        "status": _("status"),
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

        if data.get("national_id"):
            queryset = self.queryset.filter(
                national_id__istartswith=data["national_id"]
            )

        if data.get("full_name_en"):
            queryset = queryset.filter(full_name_en__istartswith=data["full_name_en"]).distinct()

        if data.get("full_name_ar"):
            queryset = queryset.filter(full_name_ar__istartswith=data["full_name_ar"]).distinct()

        if data.get("parent_phone_number"):
            queryset = queryset.filter(parent_phone_number__istartswith=data["parent_phone_number"]).distinct()

        if data.get("grade"):
            queryset = queryset.filter(grade__istartswith=data["grade"])

        if data.get("birth_date_from") and data.get("birth_date_to"):
            queryset = queryset.filter(
                date_of_birth__gte=data["birth_date_from"],
                date_of_birth__lte=data["birth_date_to"]
            )
        elif data.get("birth_date_from"):
            queryset = queryset.filter(date_of_birth__gte=data["birth_date_from"])
        elif data.get("birth_date_to"):
            queryset = queryset.filter(date_of_birth__lte=data["birth_date_to"])
        
        if data.get("status"):
            queryset = queryset.filter(is_active=data["status"])

        if data.get("parent"):
            queryset = queryset.filter(parent__user__email=data["parent"])
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(national_id__istartswith=search) |
                Q(full_name_en__istartswith=search) |
                Q(full_name_ar__istartswith=search) |
                Q(parent_phone_number__istartswith=search) |
                Q(grade__istartswith=search) 
            )
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
        if data.get("parent_phone_number"):
            descriptions.append(
                _('Student parent phone number starts with "{parent_phone_number}"').format(
                    parent_phone_number=data["parent_phone_number"]
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
        "date_of_birth": student.date_of_birth.strftime('%Y-%m-%d'),
        "grade": student.grade,
        "gender": student.gender,
        "parent_phone_number": student.parent_phone_number,
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
        if action == "active":
            student.is_active = True
            student.save()
        elif action == "inactive":
            student.is_active = False
            student.save()
        elif action == "delete":
            student.delete()

 

class StudentDetailView( DetailView):
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
            # No need to query again, we already have the student object
            student.delete()
            messages.success(request, _("Student deleted successfully"))
            return HttpResponseRedirect(reverse('dashboard:students-list'))
        except Exception as e:
            messages.error(request, _("Student cannot be deleted"))
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


class StudentUpdateView( UpdateView):
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
        # messages.success(self.request, _("Student details updated successfully"))
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
class StudentCreateView(CreateView):
    template_name = "oscar/dashboard/students/student_create.html"
    model = Student
    form_class = get_class('dashboard.students.forms', 'AddStudentForm')

    # def dispatch(self, request, *args, **kwargs):
    #     # pylint: disable=attribute-defined-outside-init
    #     self.product = get_object_or_404(
    #         self.product_model, pk=kwargs["product_pk"], is_public=True
    #     )
    #     # check permission to leave review
    #     if not self.product.is_review_permitted(request.user):
    #         if self.product.has_review_by(request.user):
    #             message = _("You have already reviewed this product!")
    #         else:
    #             message = _("You can't leave a review for this product.")
    #         messages.warning(self.request, message)
    #         return redirect(self.product.get_absolute_url())

    #     return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print("StudentCreateView")
        context = super().get_context_data(**kwargs)
        context["school"] = self.request.user.school
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        return kwargs

    def form_valid(self, form):
        form.instance.school = self.request.user.school
        response = super().form_valid(form)
        messages.success(self.request, _("Student Added Successfully."))
        return response

    def get_success_url(self):
        return reverse('dashboard:students-list')


def get_changes_between_models(model1, model2, excludes=None):
    """
    Return a dict of differences between two model instances
    """
    if excludes is None:
        excludes = []
    changes = {}
    for field in model1._meta.fields:
        if (
            isinstance(field, (fields.AutoField, fields.related.RelatedField))
            or field.name in excludes
        ):
            continue

        if field.value_from_object(model1) != field.value_from_object(model2):
            changes[field.verbose_name] = (
                field.value_from_object(model1),
                field.value_from_object(model2),
            )
    return changes


def get_change_summary(model1, model2):
    """
    Generate a summary of the changes between two address models
    """
    changes = get_changes_between_models(model1, model2, ["search_text"])
    change_descriptions = []
    for field, delta in changes.items():
        change_descriptions.append(
            _("%(field)s changed from '%(old_value)s' to '%(new_value)s'")
            % {"field": field, "old_value": delta[0], "new_value": delta[1]}
        )
    return "\n".join(change_descriptions)




class StudentImportView(TemplateView):
    template_name = 'oscar/dashboard/students/student_import.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'Upload'
        context['current_step'] = 1
        context['sample_csv_url'] = reverse('dashboard:student-sample-csv')
        return context
    
    def post(self, request, *args, **kwargs):
        if 'csv_file' not in request.FILES:
            messages.error(request, _('Please select a CSV file'))
            return self.render_to_response(self.get_context_data())
        
        csv_file = request.FILES['csv_file']
        
        # Validate file
        file_errors = StudentImportValidator.validate_file(csv_file)
        if file_errors:
            for error in file_errors:
                messages.error(request, error)
            return self.render_to_response(self.get_context_data())
        
        file_path = default_storage.save(f'temp/student_imports/{csv_file.name}', csv_file)
        request.session['import_file_path'] = file_path
        return HttpResponseRedirect(reverse('dashboard:student-import-map'))


class StudentImportMapFieldsView(TemplateView):
    template_name = 'oscar/dashboard/students/student_import_map.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_path = self.request.session.get('import_file_path')
        context['active_tab'] = 'Map'
        context['current_step'] = 2
        
        if file_path:
            with default_storage.open(file_path) as f:
                csv_reader = csv.reader(TextIOWrapper(f))
                headers = next(csv_reader)
                context['csv_headers'] = headers
                context['required_fields'] = [
                    ('full_name_en', _('Full Name (English)')),
                    ('full_name_ar', _('Full Name (Arabic)')),
                    ('national_id', _('National ID')),
                    ('grade', _('Grade')),
                    ('date_of_birth', _('Date of Birth')),
                    ('gender', _('Gender')),
                    ('parent_phone_number', _('Parent Phone Number')),
                ]
                context['optional_fields'] = [
                    ('is_active', _('Status')),
                ]
        return context

    def post(self, request, *args, **kwargs):
        field_mapping = {}
        for field, _ in self.get_context_data()['required_fields'] + self.get_context_data()['optional_fields']:
            mapped_column = request.POST.get(f'field_{field}')
            if mapped_column:
                field_mapping[field] = mapped_column
        
        request.session['field_mapping'] = field_mapping
        return HttpResponseRedirect(reverse('dashboard:student-import-preview'))

class StudentImportPreviewView(TemplateView):
    template_name = 'oscar/dashboard/students/student_import_preview.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        file_path = self.request.session.get('import_file_path')
        field_mapping = self.request.session.get('field_mapping')
        context['active_tab'] = 'Preview'
        context['current_step'] = 3
        if file_path and field_mapping:
            preview_data = []
            with default_storage.open(file_path) as f:
                csv_reader = csv.DictReader(TextIOWrapper(f))
                for i, row in enumerate(csv_reader):
                    if i >= 5:  # Preview first 5 rows
                        break
                    mapped_row = {field: row[column] for field, column in field_mapping.items()}
                    preview_data.append(mapped_row)
            context['preview_data'] = preview_data
        
        return context

    def post(self, request, *args, **kwargs):
        if 'confirm' in request.POST:
            success_count = self.process_import(request)
            # messages.success(request, _(f'Successfully imported {success_count} students'))
            request.session["success_count"] = success_count
            request.session.pop('import_file_path', None)
            request.session.pop('field_mapping', None)
            return HttpResponseRedirect(reverse('dashboard:student-import-success'))
        return self.render_to_response(self.get_context_data())

    def process_import(self, request):
        file_path = request.session.get('import_file_path')
        field_mapping = request.session.get('field_mapping')
        success_count = 0
        import_errors = {"errors": []}
        
        with default_storage.open(file_path) as f:
            csv_reader = csv.DictReader(TextIOWrapper(f))
            for row_number, row in enumerate(csv_reader, start=1):
                try:
                    student_data = {
                        field: row[column] 
                        for field, column in field_mapping.items()
                    }
                    
                    # Validate row data
                    row_errors = StudentImportValidator.validate_row(student_data, row_number)
                    if row_errors:
                        import_errors["errors"].extend(row_errors)
                        continue
                    
                    student_data['school'] = request.user.school
                    
                    if 'is_active' in student_data:
                        is_active_value = student_data['is_active'].lower()
                        student_data['is_active'] = is_active_value in ['true', '1', 'yes', 'active']
                    
                    # Check if student with same national_id already exists
                    if Student.objects.filter(national_id=student_data['national_id']).exists():
                        import_errors["errors"].append(
                            _("Row {}: Student with National ID {} already exists").format(
                                row_number, student_data['national_id']
                            )
                        )
                        continue
                    
                    Student.objects.create(**student_data)
                    success_count += 1
                    
                except Exception as e:
                    error_message = _("Row {}: Error importing student - {}").format(row_number, str(e))
                    import_errors["errors"].append(error_message)
        
        request.session["import_errors"] = import_errors
        return success_count

        
def student_sample_csv_view(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_import_template.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Full Name (English)', 'Full Name (Arabic)', 'National ID', 'Grade', 'Date of Birth', 'Gender', 'Parent Phone Number', 'Status'])
    writer.writerow(['John Doe', 'جون دو', '1234567890', 'G10', '2000-01-01', 'M', '525552368', 'Active'])
    
    return response

class StudentImportSuccessView(TemplateView):
    template_name = 'oscar/dashboard/students/student_import_success.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'Completed'
        context['current_step'] = 3
        context['success_count'] = self.request.session.get("success_count")
        context['import_errors'] = self.request.session.get("import_errors").get("errors")

        
        return context