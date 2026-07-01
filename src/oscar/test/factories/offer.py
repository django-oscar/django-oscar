import factory

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")

__all__ = [
    "RangeFactory",
    "ConditionFactory",
    "BenefitFactory",
    "ConditionalOfferFactory",
]


class RangeFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Range %d" % n)
    slug = factory.Sequence(lambda n: "range-%d" % n)

    class Meta:
        model = get_model("offer", "Range")

    @factory.post_generation
    def products(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        RangeProduct = get_model("offer", "RangeProduct")

        for product in extracted:
            RangeProduct.objects.create(product=product, range=self)


class BenefitFactory(factory.django.DjangoModelFactory):
    type = get_model("offer", "Benefit").PERCENTAGE
    value = 10
    max_affected_items = None
    range = factory.SubFactory(RangeFactory)

    class Meta:
        model = get_model("offer", "Benefit")


class ConditionFactory(factory.django.DjangoModelFactory):
    type = get_model("offer", "Condition").COUNT
    value = 10
    range = factory.SubFactory(RangeFactory)

    class Meta:
        model = get_model("offer", "Condition")


class ConditionalOfferFactory(factory.django.DjangoModelFactory):
    name = factory.Sequence(lambda n: "Test offer %d" % n)
    offer_type = ConditionalOffer.SITE
    benefit = factory.SubFactory(BenefitFactory)
    condition = factory.SubFactory(ConditionFactory)

    class Meta:
        model = get_model("offer", "ConditionalOffer")
