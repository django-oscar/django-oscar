from oscar.apps.offer import models


class ChangesOwnerName(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        condition.consume_items(basket, ())
        return models.PostOrderAction(
            "You will have your name changed to Barry!")

    def apply_deferred(self, basket):
        if basket.owner:
            basket.owner.first_name = "Barry"
            basket.owner.save()

    @property
    def description(self):
        return "Changes owners name"
