from decimal import Decimal

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
            help="Partner name for stock records (default: Demo Store)",
        )

    def handle(self, *args, **options):
        partner_name = options["partner"]

        def sr(product, price, sku):
            create_stockrecord(
                product,
                price=Decimal(price),
                num_in_stock=20,
                partner_name=partner_name,
                partner_sku=f"DEMO-{sku}",
            )

        # ── Clothing: parent + size variants ─────────────────────────────────

        for title, base_sku, base_upc, sizes, prices in [
            (
                "Classic Oxford Shirt",
                "SHIRT-OXF",
                "5901234100001",
                ["XS", "S", "M", "L", "XL"],
                ["39.95", "39.95", "39.95", "39.95", "44.95"],
            ),
            (
                "Slim Fit Chinos",
                "CHINO-SLM",
                "5901234100020",
                ["28/30", "30/30", "32/30", "32/32", "34/32", "36/32"],
                ["59.95", "59.95", "59.95", "59.95", "59.95", "64.95"],
            ),
            (
                "Merino Wool Sweater",
                "SWTR-MRN",
                "5901234100040",
                ["S", "M", "L", "XL"],
                ["89.00", "89.00", "89.00", "94.00"],
            ),
            (
                "Linen Summer Dress",
                "DRESS-LIN",
                "5901234100060",
                ["XS", "S", "M", "L"],
                ["79.95", "79.95", "79.95", "79.95"],
            ),
        ]:
            parent = create_product(
                title=title,
                product_class="Clothing",
                structure="parent",
                is_public=True,
            )
            for i, (size, price) in enumerate(zip(sizes, prices)):
                child = create_product(
                    title=f"{title} – {size}",
                    product_class="Clothing",
                    structure="child",
                    parent=parent,
                    is_public=True,
                    upc=str(int(base_upc) + i),
                )
                sr(child, price, f"{base_sku}-{size.replace('/', '-')}")

        self.stdout.write(
            self.style.SUCCESS("✓  Clothing: 4 parents with size variants")
        )

        # ── Electronics: standalone ───────────────────────────────────────────

        for title, sku, upc, price in [
            (
                "Wireless Noise-Cancelling Headphones",
                "ELEC-WNC-HP",
                "4006381333931",
                "149.00",
            ),
            ("Portable Bluetooth Speaker", "ELEC-BT-SPK", "4006381333948", "79.00"),
            ("USB-C 65W Laptop Charger", "ELEC-USBC-65", "4006381333955", "34.95"),
            ("4K HDMI Cable 2m", "ELEC-HDMI-4K", "4006381333962", "12.50"),
            (
                "Mechanical Keyboard – Compact TKL",
                "ELEC-KB-TKL",
                "4006381333979",
                "119.00",
            ),
            ("Wireless Charging Pad 15W", "ELEC-WCP-15", "4006381333986", "29.95"),
        ]:
            p = create_product(
                title=title,
                product_class="Electronics",
                structure="standalone",
                is_public=True,
                upc=upc,
            )
            sr(p, price, sku)

        self.stdout.write(self.style.SUCCESS("✓  Electronics: 6 standalone products"))

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
