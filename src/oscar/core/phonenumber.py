import warnings

from phonenumber_field.phonenumber import PhoneNumber  # noqa

from oscar.utils.deprecation import RemovedInOscar16Warning

warnings.warn(
    "The PhoneNumber class should be imported from " +
    "phonenumber_field.phonenumber module.",
    category=RemovedInOscar16Warning, stacklevel=2
)
