from oscar.apps.shipping import repository

from . import methods


class Repository(repository.Repository):
    methods = (methods.Standard, methods.Express)
