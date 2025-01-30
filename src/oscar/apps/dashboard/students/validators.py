# Add these at the top with other imports
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
import os
from datetime import datetime
from django.utils.translation import gettext_lazy as _
from io import TextIOWrapper
import csv

class StudentImportValidator:
    """
    Validator class for student imports
    """
    ALLOWED_EXTENSIONS = ['.csv']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    REQUIRED_HEADERS = ['Full Name (English)', 'Full Name (Arabic)', 'National ID', 'Grade', 'Date of Birth', 'Parent Phone Number']
    VALID_GRADES = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12']
    VALID_GENDERS = ['M', 'F']

    @classmethod
    def validate_file(cls, file):
        """Validate the uploaded file"""
        errors = []

        # Check file extension
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in cls.ALLOWED_EXTENSIONS:
            errors.append(_("Only CSV files are allowed"))

        # Check file size
        if file.size > cls.MAX_FILE_SIZE:
            errors.append(_("File size cannot exceed 5MB"))

        # Basic CSV structure validation
        try:
            # Create a copy of the file content
            content = file.read().decode('utf-8')
            file.seek(0)  # Reset file pointer
            
            # Use StringIO to create a file-like object from the content
            from io import StringIO
            csv_file = StringIO(content)
            csv_reader = csv.reader(csv_file)
            headers = next(csv_reader)
            
            # Check required headers
            missing_headers = [header for header in cls.REQUIRED_HEADERS if header not in headers]
            if missing_headers:
                errors.append(_("Missing required headers: {}").format(", ".join(missing_headers)))

        except UnicodeDecodeError:
            errors.append(_("Invalid file encoding. Please ensure the file is UTF-8 encoded"))
        except Exception as e:
            errors.append(_("Invalid CSV format: {}").format(str(e)))

        return errors

    @classmethod
    def validate_row(cls, row_data, row_number):
        """Validate a single row of data"""
        errors = []

        # National ID validation
        national_id = row_data.get('national_id')
        if not national_id:
            errors.append(_("Row {}: National ID is required").format(row_number))
        elif not re.match(r'^\d{10}$', str(national_id)):
            errors.append(_("Row {}: National ID must be 10 digits").format(row_number))

        # Name validations
        full_name_en = row_data.get('full_name_en')
        if not full_name_en:
            errors.append(_("Row {}: English name is required").format(row_number))
        elif len(full_name_en) < 2 or len(full_name_en) > 100:
            errors.append(_("Row {}: English name must be between 2 and 100 characters").format(row_number))

        full_name_ar = row_data.get('full_name_ar')
        if not full_name_ar:
            errors.append(_("Row {}: Arabic name is required").format(row_number))
        elif len(full_name_ar) < 2 or len(full_name_ar) > 100:
            errors.append(_("Row {}: Arabic name must be between 2 and 100 characters").format(row_number))
        parent_phone_number = row_data.get('parent_phone_number')
        if not parent_phone_number:
            errors.append(_("Row {}: Parent Phone Number is required").format(row_number))
        elif not parent_phone_number.isdigit() or len(parent_phone_number) != 9:
            errors.append(_("Row {}: Parent Phone Number must be exactly 9 digits").format(row_number))
        # Grade validation
        grade = row_data.get('grade')
        if not grade:
            errors.append(_("Row {}: Grade is required").format(row_number))
        elif str(grade) not in cls.VALID_GRADES:
            errors.append(_("Row {}: Invalid grade. Must be between 1 and 12").format(row_number))

        # Date of birth validation
        dob = row_data.get('date_of_birth')
        if not dob:
            errors.append(_("Row {}: Date of birth is required").format(row_number))
        else:
            try:
                parsed_date = datetime.strptime(str(dob), '%Y-%m-%d')
                if parsed_date > datetime.now():
                    errors.append(_("Row {}: Date of birth cannot be in the future").format(row_number))
            except ValueError:
                errors.append(_("Row {}: Invalid date format. Use YYYY-MM-DD").format(row_number))

        # Gender validation (optional)
        gender = row_data.get('gender')
        if gender and gender not in cls.VALID_GENDERS:
            errors.append(_("Row {}: Invalid gender. Must be 'M' or 'F'").format(row_number))

        return errors
