import os
import shutil
from datetime import date

from django.conf import settings
from django.test.utils import override_settings

from oscar.apps.order.utils import create_invoice
from oscar.core.loading import get_model
from oscar.test.testcases import WebTestCase
from oscar.test.factories import (
    CountryFactory, LegalEntityAddressFactory, LegalEntityFactory,
    UserFactory, create_order,
)

Invoice = get_model('order', 'Invoice')
LegalEntity = get_model('partner', 'LegalEntity')
LegalEntityAddress = get_model('partner', 'LegalEntityAddress')


OSCAR_INVOICE_FOLDER_FORMATTED = 'invoices/{0}/{1:02d}/'.format(date.today().year, date.today().month)
FULL_PATH_TO_INVOICES = os.path.join(settings.OSCAR_DOCUMENTS_ROOT, OSCAR_INVOICE_FOLDER_FORMATTED)


class TestInvoice(WebTestCase):

    def setUp(self):
        super(TestInvoice, self).setUp()
        self.user = UserFactory()
        self.order = create_order(number='000042', user=self.user)

        LegalEntityAddressFactory(
            legal_entity=LegalEntityFactory(),
            country=CountryFactory(),
        )

    def tearDown(self):
        super(TestInvoice, self).tearDown()
        # Remove `OSCAR_INVOICE_FOLDER` after each test
        if os.path.exists(FULL_PATH_TO_INVOICES):
            shutil.rmtree(FULL_PATH_TO_INVOICES)

    def _test_invoice_is_created(self, order_number='000043'):
        create_order(number=order_number, user=self.user)
        self.assertTrue(Invoice.objects.exists())
        invoice = Invoice.objects.first()
        return invoice

    def test_invoice_cannot_be_created_without_legal_entity(self):
        LegalEntity.objects.all().delete()

        self.assertFalse(Invoice.objects.exists())
        create_invoice(self.order)
        self.assertFalse(Invoice.objects.exists())

    def test_invoice_cannot_be_created_without_legal_entity_address(self):
        LegalEntityAddress.objects.all().delete()

        self.assertFalse(Invoice.objects.exists())
        create_invoice(self.order)
        self.assertFalse(Invoice.objects.exists())

    def test_invoice_can_be_created_with_legal_entity_and_its_address(self):
        self.assertFalse(Invoice.objects.exists())
        create_invoice(self.order)
        self.assertTrue(Invoice.objects.exists())
        invoice = Invoice.objects.first()
        # Document created and saved
        self.assertIsNotNone(invoice.document)

    @override_settings(OSCAR_INVOICE_GENERATE_AFTER_ORDER_PLACED=True)
    def test_invoice_creation_based_on_settings(self):
        invoice = self._test_invoice_is_created()
        # Document created and saved
        self.assertIsNotNone(invoice.document)

    # TEST `DocumentsStorage`

    @override_settings(OSCAR_INVOICE_GENERATE_AFTER_ORDER_PLACED=True)
    def test_invoice_document_is_not_accessible_via_url(self):
        invoice = self._test_invoice_is_created()

        another_user = UserFactory(username='another_user')
        staff_user = UserFactory(is_staff=True)
        superuser = UserFactory(is_superuser=True)

        # Invoice document is not accessible via url for any user
        for user in [self.user, another_user, staff_user, superuser]:
            with self.assertRaisesMessage(ValueError, 'This file is not accessible via a URL.'):
                self.app.get(invoice.document.url, user=user)

    @override_settings(OSCAR_INVOICE_GENERATE_AFTER_ORDER_PLACED=True)
    def test_invoice_was_saved_to_correct_folder(self):
        order_number = 'TEST_number_000d5'
        self._test_invoice_is_created(order_number=order_number)

        file_names = os.listdir(FULL_PATH_TO_INVOICES)
        self.assertEqual(len(file_names), 1)  # Only one file here
        invoice_file_name = 'invoice_{}.html'.format(order_number)
        self.assertIn(invoice_file_name, file_names)

        if os.path.exists(settings.MEDIA_ROOT):
            media_file_names = os.listdir(settings.MEDIA_ROOT)
            self.assertNotIn(invoice_file_name, media_file_names)
