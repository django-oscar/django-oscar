# On purpose raise ImportError
from django import NonExistingApp


class CatalogueApplication(NonExistingApp):
    pass
