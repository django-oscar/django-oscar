# On purpose raise ImportError
# pylint: disable=no-name-in-module
from django import NonExistingClass


class ImportErrorClass(NonExistingClass):
    pass
