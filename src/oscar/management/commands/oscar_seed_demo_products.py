from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from oscar.core.loading import get_model
from oscar.test.factories import create_product, create_stockrecord

Partner = get_model("partner", "Partner")


class Command(BaseCommand):
    help = "Seed realistic demo products for client showcasing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--partner",
            default="Demo Store",
            help="Primary partner name for stock records (default: Demo Store)",
        )
        parser.add_argument(
            "--partner2",
            default="Northside Wholesale",
            help="Secondary partner name, used for some variants/products"
            " (default: Northside Wholesale)",
        )
        parser.add_argument(
            "--partner3",
            default="Coastal Supply Co.",
            help="Third partner name, used for a few standalone products"
            " (default: Coastal Supply Co.)",
        )
        parser.add_argument(
            "--user",
            default=None,
            help="Username of an existing user to associate with partner2 and"
            " partner3 only, for testing non-staff/partner-scoped dashboard"
            " access (skipped if not given or not found).",
        )

    def handle(self, *args, **options):
        partner_name = options["partner"]
        partner2_name = options["partner2"]
        partner3_name = options["partner3"]

        partner_users = None
        username = options["user"]
        if username:
            User = get_user_model()
            user = User.objects.filter(**{User.USERNAME_FIELD: username}).first()
            if user is None:
                self.stdout.write(
                    self.style.WARNING(
                        f"No user found for --user={username!r}, skipping."
                    )
                )
            else:
                partner_users = [user]
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓  {username} will be associated with"
                        f" {partner2_name!r} and {partner3_name!r} only"
                    )
                )

        def sr(product, price, sku, partner=None):
            create_stockrecord(
                product,
                price=Decimal(price),
                num_in_stock=20,
                partner_name=partner or partner_name,
                partner_sku=f"DEMO-{sku}",
                partner_users=(
                    partner_users if partner and partner != partner_name else None
                ),
            )

        # ── Clothing: parent + size variants, split across partners ───────────
        # "Classic Oxford Shirt" has some sizes stocked by partner2 to exercise
        # the "variants from another partner are hidden" dashboard behaviour.

        for title, base_sku, base_upc, sizes, prices, size_partners in [
            (
                "Classic Oxford Shirt",
                "SHIRT-OXF",
                "5901234100001",
                ["XS", "S", "M", "L", "XL"],
                ["39.95", "39.95", "39.95", "39.95", "44.95"],
                [
                    partner_name,
                    partner_name,
                    partner_name,
                    partner2_name,
                    partner2_name,
                ],
            ),
            (
                "Slim Fit Chinos",
                "CHINO-SLM",
                "5901234100020",
                ["28/30", "30/30", "32/30", "32/32", "34/32", "36/32"],
                ["59.95", "59.95", "59.95", "59.95", "59.95", "64.95"],
                [partner_name] * 6,
            ),
            (
                "Merino Wool Sweater",
                "SWTR-MRN",
                "5901234100040",
                ["S", "M", "L", "XL"],
                ["89.00", "89.00", "89.00", "94.00"],
                [partner_name] * 4,
            ),
            (
                "Linen Summer Dress",
                "DRESS-LIN",
                "5901234100060",
                ["XS", "S", "M", "L"],
                ["79.95", "79.95", "79.95", "79.95"],
                [partner_name] * 4,
            ),
        ]:
            parent = create_product(
                title=title,
                product_class="Clothing",
                structure="parent",
                is_public=True,
            )
            for i, (size, price, size_partner) in enumerate(
                zip(sizes, prices, size_partners)
            ):
                child = create_product(
                    title=f"{title} – {size}",
                    product_class="Clothing",
                    structure="child",
                    parent=parent,
                    is_public=True,
                    upc=str(int(base_upc) + i),
                )
                sr(
                    child,
                    price,
                    f"{base_sku}-{size.replace('/', '-')}",
                    partner=size_partner,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "✓  Clothing: 4 parents with size variants"
                f" (Classic Oxford Shirt split between {partner_name!r} and"
                f" {partner2_name!r})"
            )
        )

        # ── Electronics: standalone, mostly primary partner, a few from partner3 ──

        for title, sku, upc, price, product_partner in [
            (
                "Wireless Noise-Cancelling Headphones",
                "ELEC-WNC-HP",
                "4006381333931",
                "149.00",
                partner_name,
            ),
            (
                "Portable Bluetooth Speaker",
                "ELEC-BT-SPK",
                "4006381333948",
                "79.00",
                partner_name,
            ),
            (
                "USB-C 65W Laptop Charger",
                "ELEC-USBC-65",
                "4006381333955",
                "34.95",
                partner_name,
            ),
            (
                "4K HDMI Cable 2m",
                "ELEC-HDMI-4K",
                "4006381333962",
                "12.50",
                partner3_name,
            ),
            (
                "Mechanical Keyboard – Compact TKL",
                "ELEC-KB-TKL",
                "4006381333979",
                "119.00",
                partner_name,
            ),
            (
                "Wireless Charging Pad 15W",
                "ELEC-WCP-15",
                "4006381333986",
                "29.95",
                partner3_name,
            ),
        ]:
            p = create_product(
                title=title,
                product_class="Electronics",
                structure="standalone",
                is_public=True,
                upc=upc,
            )
            sr(p, price, sku, partner=product_partner)

        self.stdout.write(
            self.style.SUCCESS(
                "✓  Electronics: 6 standalone products"
                f" (2 stocked entirely by {partner3_name!r})"
            )
        )

        # ── Books: parent + format variants ──────────────────────────────────

        for title, base_sku, base_upc, formats in [
            (
                "The Art of Simple Living",
                "BOOK-ASL",
                "9780000000001",
                [("Hardcover", "24.95"), ("Paperback", "14.95"), ("E-book", "8.99")],
            ),
            (
                "Python for Data Science",
                "BOOK-PDS",
                "9780000000010",
                [("Hardcover", "49.95"), ("Paperback", "34.95"), ("E-book", "19.99")],
            ),
            (
                "Mindful Business Leadership",
                "BOOK-MBL",
                "9780000000020",
                [("Hardcover", "32.00"), ("Paperback", "19.95"), ("E-book", "12.99")],
            ),
        ]:
            parent = create_product(
                title=title,
                product_class="Books",
                structure="parent",
                is_public=True,
            )
            for i, (fmt, price) in enumerate(formats):
                child = create_product(
                    title=f"{title} ({fmt})",
                    product_class="Books",
                    structure="child",
                    parent=parent,
                    is_public=True,
                    upc=str(int(base_upc) + i),
                )
                sr(child, price, f"{base_sku}-{fmt[:3].upper()}")

        self.stdout.write(
            self.style.SUCCESS("✓  Books: 3 parents with format variants")
        )

        # ── Unpublished products: demo the bulk-publish action ────────────────

        for title, sku, upc, price in [
            ("Linen Trousers – Coming Soon", "CLOTH-LIN-TR", "5901234200001", "69.95"),
            ("Canvas Tote Bag", "ACCS-TOTE", "5901234200002", "19.95"),
            ("Bamboo Water Bottle 750ml", "KITC-BWBT", "5901234200003", "24.00"),
            ("Recycled Wool Beanie", "CLOTH-BNEI", "5901234200004", "22.00"),
        ]:
            p = create_product(
                title=title,
                product_class="Accessories",
                structure="standalone",
                is_public=False,
                upc=upc,
            )
            sr(p, price, sku)

        self.stdout.write(
            self.style.SUCCESS(
                "✓  Accessories: 4 unpublished standalones (bulk-publish demo)"
            )
        )
        self.stdout.write(
            self.style.SUCCESS("\nDone. Run the dashboard to see the results.")
        )
