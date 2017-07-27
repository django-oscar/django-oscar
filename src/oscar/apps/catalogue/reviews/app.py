from oscar.core.application import Application


class ProductReviewsApplication(Application):
    name = None
    hidable_feature_name = "reviews"


application = ProductReviewsApplication()
