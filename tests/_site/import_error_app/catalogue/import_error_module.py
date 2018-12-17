# On purpose raise ImportError
from django import NonExistingClass


class ImportErrorClass(NonExistingClass):
    pass
