# tasks.py
import os
from celery import shared_task
from django.core.files.storage import default_storage
import csv
from io import TextIOWrapper
from .validators import StudentImportValidator
from django.utils.translation import gettext_lazy as _
from oscar.core.loading import get_class, get_model

Student = get_model("school", "Student")


@shared_task(bind=True)
def process_student_import(self, file_path, field_mapping, school_id):
    """
    Celery task to process the student import from a CSV file.
    """
    success_count = 0
    errors = []

    with default_storage.open(file_path) as f:
        csv_reader = csv.DictReader(TextIOWrapper(f))
        total_rows = sum(1 for _ in csv_reader)
        f.seek(0)
        next(csv_reader)

        for row_number, row in enumerate(csv_reader, start=1):
            try:
                # Map CSV columns to student fields
                student_data = {
                    field: row[column] for field, column in field_mapping.items()
                }

                # Handle the is_active field conversion
                if "is_active" in student_data:
                    status_value = student_data["is_active"].lower().strip()
                    if status_value in ("true", "active", "1", "yes"):
                        student_data["is_active"] = True
                    elif status_value in ("false", "inactive", "0", "no"):
                        student_data["is_active"] = False
                    else:
                        raise ValueError(
                            "Invalid status value. Must be Active/Inactive or True/False"
                        )

                # Rest of your validation and import logic...
                row_errors = StudentImportValidator.validate_row(
                    student_data, row_number
                )
                if row_errors:
                    errors.extend(row_errors)
                    continue

                # Add school information
                student_data["school_id"] = school_id

                # Handle photo
                if "photo" in student_data and student_data["photo"]:
                    photo_name = student_data["photo"]
                    photo_path = os.path.join("student_images", photo_name)
                    student_data["photo"] = photo_path

                # Check for existing student
                if Student.objects.filter(
                    national_id=student_data["national_id"]
                ).exists():
                    errors.append(
                        _("Row {}: Student with National ID {} already exists").format(
                            row_number, student_data["national_id"]
                        )
                    )
                    continue

                # Create the student
                Student.objects.create(**student_data)
                success_count += 1

            except Exception as e:
                errors.append(
                    _("Row {}: Error importing student - {}").format(row_number, str(e))
                )

            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={
                    "current": row_number,
                    "total": total_rows,
                    "status": f"Processed {row_number}/{total_rows} rows",
                },
            )
    # Update progress
    self.update_state(
        state="SUCCESS",
        meta={
            "current": row_number,
            "total": total_rows,
            "status": f"Processed {row_number}/{total_rows} rows",
            "errors": errors,
        },
    )
    return {
        "success_count": success_count,
        "errors": errors,
    }
