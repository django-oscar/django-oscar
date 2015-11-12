# -*- coding: utf-8 -*-
from optparse import make_option
import sys

from django.core.management.base import BaseCommand, CommandError

from oscar.core.loading import get_model

Country = get_model('address', 'Country')


class Command(BaseCommand):
    help = "Populates the list of countries with data from pycountry."
    # TODO: Allow setting locale to fetch country names in right locale
    # https://code.djangoproject.com/ticket/6376

    option_list = BaseCommand.option_list + (
        make_option(
            '--no-shipping',
            action='store_false',
            dest='is_shipping',
            default=True,
            help="Don't mark countries for shipping"),
        make_option(
            '--initial-only',
            action='store_true',
            dest='is_initial_only',
            default=False,
            help="Exit quietly without doing anything if countries were already populated."),
    )

    def handle(self, *args, **options):
        try:
            import pycountry
        except ImportError:
            raise CommandError(
                "You are missing the pycountry library. Install it with "
                "'pip install pycountry'")

        if Country.objects.exists():
            if options.get('is_initial_only', False):
                # exit quietly, as the initial load already seems to have happened.
                self.stdout.write("Countries already populated; nothing to be done.")
                sys.exit(0)
            else:
                raise CommandError(
                    "You already have countries in your database. This command "
                    "currently does not support updating existing countries.")

        countries = [
            Country(
                iso_3166_1_a2=country.alpha2,
                iso_3166_1_a3=country.alpha3,
                iso_3166_1_numeric=country.numeric,
                printable_name=country.name,
                name=getattr(country, 'official_name', ''),
                is_shipping_country=options['is_shipping'])
            for country in pycountry.countries]

        Country.objects.bulk_create(countries)
        self.stdout.write("Successfully added %s countries." % len(countries))
