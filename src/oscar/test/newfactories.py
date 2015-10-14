import warnings

from oscar.test.factories.address import *  # noqa
from oscar.test.factories.basket import *  # noqa
from oscar.test.factories.catalogue import *  # noqa
from oscar.test.factories.contrib import *  # noqa
from oscar.test.factories.customer import *  # noqa
from oscar.test.factories.offer import *  # noqa
from oscar.test.factories.order import *  # noqa
from oscar.test.factories.partner import *  # noqa
from oscar.test.factories.payment import *  # noqa
from oscar.test.factories.utils import *  # noqa
from oscar.test.factories.voucher import *  # noqa

message = (
    "Module '%s' is deprecated and will be removed in the next major version "
    "of django-oscar"
) % __name__

warnings.warn(message, PendingDeprecationWarning)
