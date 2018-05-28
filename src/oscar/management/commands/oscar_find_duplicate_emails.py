from collections import Counter

from django.core.management.base import BaseCommand

from oscar.core.compat import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = ('Finds email addresses that are used by more than one user. '
            'Casing is ignored.')

    def handle(self, *args, **options):
        emails = User.objects.values_list('email', flat=True)
        emails = map(lambda x: x.lower(), emails)
        duplicates = sorted([
            (email, count) for email, count in Counter(emails).most_common()
            if count > 1])
        if duplicates:
            for email, __ in duplicates:
                users = User.objects.filter(email__iexact=email)
                user_strings = [
                    "{} (#{})".format(user.get_username(), user.pk)
                    for user in users]
                print("{email} is assigned to: {pk_list}".format(
                    email=email, pk_list=", ".join(user_strings)))
        else:
            print("No duplicate email addresses found!")
