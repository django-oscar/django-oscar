import factory

from oscar.core.compat import get_user_model
from oscar.core.loading import get_model

__all__ = ['ProductAlertFactory', 'UserFactory']


class ProductAlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_model('customer', 'ProductAlert')

    product = factory.SubFactory('oscar.test.factories.ProductFactory')
    user = factory.SubFactory('oscar.test.factories.customer.UserFactory')
    status = Meta.model.ACTIVE


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'the_j_meister nummer %d' % n)
    email = factory.Sequence(lambda n: 'example_%s@example.com' % n)
    first_name = 'joseph'
    last_name = 'winterbottom'
    password = factory.PostGenerationMethodCall('set_password', 'skelebrain')
    is_active = True
    is_superuser = False
    is_staff = False

    class Meta:
        model = get_user_model()
