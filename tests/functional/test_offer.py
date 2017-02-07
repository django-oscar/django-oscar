from oscar.test.testcases import WebTestCase


class TestTheOfferListPage(WebTestCase):

    def test_exists(self):
        response = self.app.get('/offers/')
        self.assertEqual(200, response.status_code)
