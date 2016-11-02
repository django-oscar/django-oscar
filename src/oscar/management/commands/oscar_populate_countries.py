# -*- coding: utf-8 -*-
import sys
from optparse import make_option

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
                num_updated = 0
                num_created = 0
                for country in pycountry.countries:
                    oscar_country, created = Country.objects.get_or_create(
                        iso_3166_1_a2=country.alpha2
                    )
                    oscar_country.iso_3166_1_a2 = country.alpha2
                    oscar_country.iso_3166_1_a3 = country.alpha3
                    oscar_country.iso_3166_1_numeric = country.numeric
                    oscar_country.printable_name = country.name
                    oscar_country.name = getattr(country, 'official_name', country.name)
                    oscar_country.is_shipping_country = options['is_shipping']
                    oscar_country.save()

                    if created:
                        num_created += 1
                    else:
                        num_updated += 1

                self.stdout.write(
                    "Successfully updated %s, created %s countries." % (num_updated, num_created)
                )
        else:
            countries = [
                Country(
                    iso_3166_1_a2=country.alpha2,
                    iso_3166_1_a3=country.alpha3,
                    iso_3166_1_numeric=country.numeric,
                    printable_name=country.name,
                    name=getattr(country, 'official_name', country.name),
                    is_shipping_country=options['is_shipping'])
                for country in pycountry.countries]

            Country.objects.bulk_create(countries)
            self.stdout.write("Successfully added %s countries." % len(countries))
