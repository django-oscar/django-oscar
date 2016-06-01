# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from oscar.core.loading import get_model

Category = get_model('catalogue', 'Category')


class Command(BaseCommand):
    help = "Populates the full_name and full_slug fields for Category."

    def handle(self, *args, **options):
        Category.denormalise_fields()
