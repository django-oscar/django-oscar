from oscar.apps.offer import models


class ChangesOwnerName(models.Benefit):

    class Meta:
        proxy = True

    def apply(self, basket, condition, offer=None):
        condition.consume_items(offer, basket, ())
        return models.PostOrderAction(
            "You will have your name changed to Barry!")

    def apply_deferred(self, basket, order, application):
        if basket.owner:
            basket.owner.first_name = "Barry"
            basket.owner.save()
        return "Your name has been changed to Barry!"

    @property
    def description(self):
        return "Changes owners name"

    name = description
