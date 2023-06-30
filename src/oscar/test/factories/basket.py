import factory

from oscar.core.loading import get_class, get_model

Selector = get_class("partner.strategy", "Selector")


__all__ = ["BasketFactory", "BasketLineAttributeFactory"]


class BasketFactory(factory.django.DjangoModelFactory):
    # pylint: disable=unused-argument, W0201
    @factory.post_generation
    def set_strategy(self, create, extracted, **kwargs):
        # Load default strategy (without a user/request)
        self.strategy = Selector().strategy()

    class Meta:
        model = get_model("basket", "Basket")


class BasketLineAttributeFactory(factory.django.DjangoModelFactory):
    option = factory.SubFactory("oscar.test.factories.OptionFactory")

    class Meta:
        model = get_model("basket", "LineAttribute")
