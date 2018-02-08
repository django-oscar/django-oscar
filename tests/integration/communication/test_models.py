import pytest
from django.core import exceptions

from oscar.core.loading import get_model

CommunicationEventType = get_model('communication', 'CommunicationEventType')


def test_communication_event_type_code_forbids_hyphens():
    ctype = CommunicationEventType(code="A-B")
    with pytest.raises(exceptions.ValidationError):
        ctype.full_clean()
