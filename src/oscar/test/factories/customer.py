import factory
from faker import Faker

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

__all__ = ['ProductAlertFactory', 'UserFactory']

USER_PASSWORD = 'oscar'
faker = Faker()


class ProductAlertFactory(factory.DjangoModelFactory):
    class Meta:
        model = get_model('customer', 'ProductAlert')

    product = factory.SubFactory('oscar.test.factories.ProductFactory')
    user = factory.SubFactory('oscar.test.factories.customer.UserFactory')
    status = Meta.model.ACTIVE


class UserFactory(factory.DjangoModelFactory):
    username = factory.LazyAttribute(lambda x: faker.user_name())
    email = factory.LazyAttribute(lambda x: faker.email())
    first_name = factory.LazyAttribute(lambda x: faker.first_name())
    last_name = factory.LazyAttribute(lambda x: faker.last_name())
    is_active = True

    class Meta:
        model = get_user_model()

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        self.set_password(USER_PASSWORD)
        self.save()
