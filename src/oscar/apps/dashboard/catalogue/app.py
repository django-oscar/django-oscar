
from oscar.core.application import Application


class CatalogueApplication(Application):
    name = None

    def get_urls(self):
        urls = [

        ]
        return self.post_process_urls(urls)


application = CatalogueApplication()
