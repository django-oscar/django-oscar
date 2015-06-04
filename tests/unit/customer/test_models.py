import pytest
from django.core import exceptions

from oscar.apps.customer import models


def test_communication_event_type_code_forbids_hyphens():
    ctype = models.CommunicationEventType(code="A-B")
    with pytest.raises(exceptions.ValidationError):
        ctype.full_clean()
